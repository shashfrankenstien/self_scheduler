import os
import json
import traceback
from flask import Flask, send_file, request, redirect, make_response
from itsdangerous import URLSafeSerializer

from capture import print_capture
from models import SelfSchedulerDB
from models.project import SUPPORTED_LANGUAGES


CWD = os.path.dirname(os.path.abspath(__file__))

workspace_path = os.environ.get('SS_WORKSPACE_PATH', 'projects')
workspace_path = os.path.realpath(workspace_path)
db = SelfSchedulerDB(workspace_path)
db.create_tables()


app = Flask(__name__)

crypt = URLSafeSerializer("secret")


def fillTemplate(htmlText, **kwargs):
	for arg in kwargs:
		htmlText = htmlText.replace("{{ "+arg+" }}", str(kwargs[arg]))
	return htmlText


def openHTML(fileName, **kwargs):
	with open(fileName, 'r') as f:
		templateText = f.read()
	return make_response(fillTemplate(templateText, **kwargs))




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
	return openHTML(
		os.path.join(CWD, 'web', 'profile.html'),
		face=u.gravatar_url,
		name=f"{u.first_name} {u.last_name}",
	)


@app.route("/login", methods=['GET','POST'])
def login():
	if request.method == 'GET':
		return send_file(os.path.join(CWD, 'web', 'login.html'))

	data = json.loads(request.data)
	print(data)
	u = db.login_user(data.get('email'), data.get('password'))
	print(u)
	resp = make_response(json.dumps({'success': True}))
	set_cookie_token(resp, user=u)
	return resp


@app.route("/signup", methods=['POST'])
def signup():
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


@app.route("/project/new", methods=['POST'])
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
	request.user.get_project(project_hash)  # basic file structure init
	return openHTML(os.path.join(CWD, 'web', 'project.html'), project_hash=project_hash)


@app.route("/project/<project_hash>/tree", methods=['GET'])
@cookie_login_json
def tree(project_hash):
	P = request.user.get_project(project_hash)
	return json.dumps({'success': P.struct_to_dict()})



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
	msgs = []
	def _cb(msg):
		msgs.append(str(msg))

	with print_capture(_cb):
		P = request.user.get_project(project_hash)
		P.run()

	return json.dumps({'success': ''.join(msgs)})





if __name__ == '__main__':
	app.run("0.0.0.0", port=5000)
