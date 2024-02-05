import os
import json
import traceback
import argparse

from flask import Flask, send_file, request, redirect, make_response, Response
from itsdangerous import URLSafeSerializer

from app import get_ss_db_object
from app.project import SUPPORTED_LANGUAGES


CWD = os.path.dirname(os.path.abspath(__file__))


parser = argparse.ArgumentParser(__name__)
parser.add_argument("--workspace-path", "-w", help="Path to workspace directory", type=str, default=None)
parser.add_argument("--signup-enable", help="Run app with signup page enabled", action="store_true")
args = parser.parse_args()


WORKSPACE_PATH = args.workspace_path or os.environ.get('SS_WORKSPACE_PATH', 'projects')
SIGNUP_ENABLED = args.signup_enable or os.environ.get('SS_SIGNUP_ENABLED') == '1'

print("WORKSPACE_PATH:", WORKSPACE_PATH)
print("SIGNUP_ENABLED:", SIGNUP_ENABLED)



app = Flask(__name__)
crypt = URLSafeSerializer("secret")

db = get_ss_db_object(os.path.realpath(WORKSPACE_PATH))


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
	request.user.logged_in = True


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
			return json.dumps({'success': f(*args, **kwargs)})
		except Exception as e:
			traceback.print_exc()
			return json.dumps({'error': str(e)})

	_wrapper.__name__ = f.__name__
	return _wrapper


def cookie_login_stream(f):
	def _wrapper(*args, **kwargs):
		try:
			set_user_from_cookie()
			return f(*args, **kwargs)
		except Exception as e:
			return json.dumps({'error': str(e)})

	_wrapper.__name__ = f.__name__
	return _wrapper




@app.route("/static/<folder>/<filename>", methods=['GET'])
def static_files(folder, filename):
	return send_file(os.path.join(CWD, 'web', folder, filename))


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
	u = db.get_user(data.get('email')).login(data.get('password'))
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




# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Project API
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

@app.route("/projects", methods=['GET'])
@cookie_login_json
def list_projects():
	return request.user.get_projects_dict()


@app.route("/projects/new", methods=['POST'])
@cookie_login_json
def new_project():
	project_name = request.json['name']
	project_descr = request.json['descr']
	P = request.user.create_new_project(project_name, project_descr)  # basic file structure init
	return P.name_hash


@app.route("/projects/rename", methods=['POST'])
@cookie_login_json
def rename_project():
	P = request.user.get_project(request.json['project_hash'])
	return P.rename(request.json['new_name'])


@app.route("/projects/delete", methods=['POST'])
@cookie_login_json
def delete_project():
	P = request.user.get_project(request.json['project_hash'].strip())
	return P.delete()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

@app.route("/project/<project_hash>", methods=['GET'])
@cookie_login
def open_project(project_hash):
	request.user.get_project(project_hash)  # basic file structure init
	# P.create_default_entry_point()
	# P.get_properties()
	return SimpleTemplate.send_file(os.path.join(CWD, 'web', 'project.html'), project_hash=project_hash)


@app.route("/project/<project_hash>/tree", methods=['GET'])
@cookie_login_json
def tree(project_hash):
	P = request.user.get_project(project_hash)
	return P.get_file_struct_dict()


@app.route("/project/<project_hash>/properties", methods=['GET'])
@cookie_login_json
def properties(project_hash):
	P = request.user.get_project(project_hash)
	return P.get_properties()


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
	return res


@app.route("/project/<project_hash>/file/src", methods=['POST'])
@cookie_login_json
def file_src(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	path = str(data['path']).strip()
	return P.get_file_src(path)


@app.route("/project/<project_hash>/file/save", methods=['POST'])
@cookie_login_json
def save_file(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	res = P.save_file(data['path'], data['src'])
	return res


@app.route("/project/<project_hash>/file/delete", methods=['POST'])
@cookie_login_json
def delete_file(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	res = P.delete_file(data['path'])
	return res



@app.route("/project/<project_hash>/folder/new", methods=['POST'])
@cookie_login_json
def new_folder(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	name = str(data['name']).strip()

	res = P.new_folder(data['path'], name)
	return res


@app.route("/project/<project_hash>/folder/delete", methods=['POST'])
@cookie_login_json
def delete_folder(project_hash):
	P = request.user.get_project(project_hash)
	res = P.delete_folder(request.json['path'])
	return res


@app.route("/project/<project_hash>/object/rename", methods=['POST'])
@cookie_login_json
def rename_object(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	name = str(data['name']).strip()

	res = P.rename_object(data['path'], name)
	return res


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

@app.route("/project/<project_hash>/entry-points", methods=['GET'])
@cookie_login_json
def all_entrypoints(project_hash):
	P = request.user.get_project(project_hash)
	return P.get_all_entry_points()


@app.route("/project/<project_hash>/entry-point/new", methods=['POST'])
@cookie_login_json
def new_entrypoint(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	file = str(data['file']).strip()
	func = str(data['func']).strip()
	is_default = data.get('make_default', False)
	P.create_entry_point(file, func, is_default=is_default)
	return P.get_all_entry_points()


@app.route("/project/<project_hash>/entry-point/delete", methods=['POST'])
@cookie_login_json
def delete_entrypoint(project_hash):
	P = request.user.get_project(project_hash)
	epid = request.json['epid']
	P.delete_entry_point(epid)
	return True


@app.route("/project/<project_hash>/schedule/new", methods=['POST'])
@cookie_login_json
def new_schedule(project_hash):
	P = request.user.get_project(project_hash)
	data = request.json
	epid = str(data['epid']).strip()
	every = str(data['every']).strip()
	at = str(data['at']).strip()
	tzname = data.get('tzname', None)
	P.create_schedule(epid, every, at, tzname)
	return P.get_full_schedule()


@app.route("/project/<project_hash>/schedule/delete", methods=['POST'])
@cookie_login_json
def delete_schedule(project_hash):
	P = request.user.get_project(project_hash)
	epid = request.json['epid']
	sched_id = request.json['sched_id']
	P.delete_schedule(epid, sched_id)
	return True



# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


@app.route("/project/<project_hash>/run", methods=['POST'])
@cookie_login_stream
def run(project_hash):
	# print(app.url_map)
	P = request.user.get_project(project_hash)
	epid = request.json.get('epid')
	# msg_queue = queue.Queue()
	# run_thread = P.create_run_thread(epid, msg_queue=msg_queue)

	# def progress():
	# 	run_thread.start()
	# 	while run_thread.is_alive():
	# 		yield msg_queue.get()
	# 	while not msg_queue.empty():
	# 		yield msg_queue.get()
	# 	run_thread.join()

	return Response(P.run_with_progress(epid))





if __name__ == '__main__':
	app.run("0.0.0.0", port=5000)
