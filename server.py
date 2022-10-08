import os
import json
import queue
import traceback
import argparse

from flask import Flask, send_file, request, redirect, make_response, Response
from itsdangerous import URLSafeSerializer

from models import SelfSchedulerDB
from models.project import SUPPORTED_LANGUAGES


CWD = os.path.dirname(os.path.abspath(__file__))


parser = argparse.ArgumentParser(__name__)
parser.add_argument("--workspace-path", "-w", help="Path to workspace directory", type=str, default=None)
parser.add_argument("--signup-enable", help="Run app with signup page enabled", action="store_true")
args = parser.parse_args()


if args.workspace_path:
	WORKSPACE_PATH = args.workspace_path
else:
	WORKSPACE_PATH = os.environ.get('SS_WORKSPACE_PATH', 'projects')

if args.signup_enable:
	SIGNUP_ENABLED = True
else:
	SIGNUP_ENABLED = os.environ.get('SS_SIGNUP_ENABLED') == '1'


app = Flask(__name__)
crypt = URLSafeSerializer("secret")

db = SelfSchedulerDB(os.path.realpath(WORKSPACE_PATH))
db.create_tables()


class SimpleTemplate:

	@staticmethod
	def render(htmlText, **kwargs):
		for arg in kwargs:
			htmlText = htmlText.replace("{{ "+arg+" }}", str(kwargs[arg]))
		return htmlText

	@staticmethod
	def render_file(fileName, **kwargs):
		with open(fileName, 'r') as f:
			templateText = f.read()
		return SimpleTemplate.render(templateText, **kwargs)


	@staticmethod
	def send_file(fileName, **kwargs):
		return make_response(SimpleTemplate.render_file(fileName, **kwargs))




@app.errorhandler(Exception)
def all_errors(e):
	if request.url.endswith(".ico"):
		return "Not found", 404
	print(traceback.format_exc())
	return json.dumps({'error': str(e)})


def set_cookie_token(resp, user):
	enc = crypt.dumps({'id': user.user_id, 'email': user.email})
	resp.set_cookie('Authorization', enc)


def set_user_from_cookie():
	auth = request.cookies.get("Authorization")
	dec = crypt.loads(auth)
	request.user = db.get_user(dec['email'])


def cookie_login(f):
	def _wrapper(*args, **kwargs):
		try:
			set_user_from_cookie()
		except Exception as e:
			print(e)
			return redirect("/login")
		return f(*args, **kwargs)
	_wrapper.__name__ = f.__name__
	return _wrapper


def cookie_login_json(f):
	def _wrapper(*args, **kwargs):
		try:
			set_user_from_cookie()
		except Exception as e:
			return json.dumps({'error': str(e)})

		return f(*args, **kwargs)
	_wrapper.__name__ = f.__name__
	return _wrapper




@app.route("/", methods=['GET'])
@cookie_login
def home():
	u = request.user
	return SimpleTemplate.send_file(
		os.path.join(CWD, 'web', 'profile.html'),
		face=u.gravatar_url,
		name=f"{u.first_name} {u.last_name}",
	)


@app.route("/login", methods=['GET','POST'])
def login():
	if request.method == 'GET':
		signup_link = ''
		signup_content = 'DISABLED'
		if SIGNUP_ENABLED:
			signup_link = '''<a href="#" onclick="showSignup()">Signup</a>'''
			signup_content = SimpleTemplate.render_file(os.path.join(CWD, 'web', 'signup_content.html'))

		return SimpleTemplate.send_file(
			os.path.join(CWD, 'web', 'login.html'),
			signup_link=signup_link,
			signup_content=signup_content
		)

	data = json.loads(request.data)
	print(data)
	u = db.login_user(data.get('email'), data.get('password'))
	print(u)
	resp = make_response(json.dumps({'success': True}))
	set_cookie_token(resp, user=u)
	return resp


@app.route("/signup", methods=['POST'])
def signup():
	if not SIGNUP_ENABLED:
		raise NotImplementedError("Action is disabled")
	data = json.loads(request.data)
	print(data)
	u = db.create_new_user(data.get('first_name'), data.get('last_name'), data.get('email'), data.get('password'))
	print(u)
	resp = make_response(json.dumps({'success': True}))
	set_cookie_token(resp, user=u)
	return resp





@app.route("/static/<folder>/<filename>", methods=['GET'])
def static_files(folder, filename):
	return send_file(os.path.join(CWD, 'web', folder, filename))


# Project API
@app.route("/projects", methods=['GET'])
@cookie_login_json
def list_projects():
	projs = request.user.get_projects_dict()
	return json.dumps({'success': projs})


@app.route("/projects/new", methods=['POST'])
@cookie_login_json
def new_project():
	data = json.loads(request.data)
	project_name = data['name']
	project_descr = data['descr']
	P = request.user.create_new_project(project_name, project_descr)  # basic file structure init
	return json.dumps({'success': P.name_hash})


@app.route("/project/<project_hash>", methods=['GET'])
@cookie_login
def open_project(project_hash):
	P = request.user.get_project(project_hash)  # basic file structure init
	# P.create_default_entry_point()
	P.get_properties()
	return SimpleTemplate.send_file(os.path.join(CWD, 'web', 'project.html'), project_hash=project_hash)


@app.route("/project/<project_hash>/tree", methods=['GET'])
@cookie_login_json
def tree(project_hash):
	P = request.user.get_project(project_hash)
	return json.dumps({'success': P.get_file_struct_dict()})


@app.route("/project/<project_hash>/properties", methods=['GET'])
@cookie_login_json
def properties(project_hash):
	P = request.user.get_project(project_hash)
	return json.dumps({'success': P.get_properties()})


@app.route("/project/<project_hash>/file/new", methods=['POST'])
@cookie_login_json
def new_file(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	name = str(data['name']).strip()

	ext = os.path.splitext(name)[-1]
	if ext not in SUPPORTED_LANGUAGES:
		raise NotImplementedError("support for file type not implemented")

	res = P.new_file(data['path'], name)
	return json.dumps({'success': res})


@app.route("/project/<project_hash>/file/save", methods=['POST'])
@cookie_login_json
def save_file(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	res = P.save_file(data['path'], data['src'])
	return json.dumps({'success': res})


@app.route("/project/<project_hash>/file/delete", methods=['POST'])
@cookie_login_json
def delete_file(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	res = P.delete_file(data['path'])
	return json.dumps({'success': res})



@app.route("/project/<project_hash>/folder/new", methods=['POST'])
@cookie_login_json
def new_folder(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	name = str(data['name']).strip()

	res = P.new_folder(data['path'], name)
	return json.dumps({'success': res})


@app.route("/project/<project_hash>/folder/delete", methods=['POST'])
@cookie_login_json
def delete_folder(project_hash):
	P = request.user.get_project(project_hash)
	res = P.delete_folder(request.json['path'])
	return json.dumps({'success': res})


@app.route("/project/<project_hash>/rename", methods=['POST'])
@cookie_login_json
def rename(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	name = str(data['name']).strip()

	res = P.rename(data['path'], name)
	return json.dumps({'success': res})


@app.route("/project/<project_hash>/run", methods=['GET'])
@cookie_login_json
def run(project_hash):
	P = request.user.get_project(project_hash)
	msg_queue = queue.Queue()
	run_thread = P.create_run_thread(msg_queue=msg_queue)

	def progress():
		run_thread.start()
		while run_thread.is_alive():
			yield msg_queue.get()
		while not msg_queue.empty():
			yield msg_queue.get()
		run_thread.join()

	return Response(progress())





if __name__ == '__main__':
	app.run("0.0.0.0", port=5000)
