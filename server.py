import os
import json
import traceback
import configparser
from flask import Flask, send_file, request, redirect, make_response
from itsdangerous import URLSafeSerializer

from capture import print_capture
from models import SelfSchedulerDB
from models.project import SUPPORTED_LANGUAGES


CWD = os.path.dirname(os.path.abspath(__file__))

default_config = {'workspace_path': 'projects'}
config = configparser.ConfigParser(defaults=default_config)
config.read(os.path.join(CWD, 'config.ini'))


workspace_path = os.path.realpath(config['DEFAULT']['workspace_path'])
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
	return fillTemplate(templateText, **kwargs)




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
	return send_file(os.path.join(CWD, 'web', 'index.html'))


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
	data = json.loads(request.data)
	print(data)
	u = db.create_new_user(data.get('first_name'), data.get('last_name'), data.get('email'), data.get('password'))
	print(u)
	resp = make_response(json.dumps({'success': True}))
	set_cookie_token(resp, user=u)
	return resp





@app.route("/static/<folder>/<filename>", methods=['GET'])
@cookie_login
def static_files(folder, filename):
	return send_file(os.path.join(CWD, 'web', folder, filename))


# Project API
@app.route("/project/<project_name>", methods=['GET'])
@cookie_login
def open_project(project_name):
	request.user.get_project(project_name)  # basic file structure init
	return openHTML(os.path.join(CWD, 'web', 'project.html'), project_name=project_name)


@app.route("/project/<project_name>/tree", methods=['GET'])
@cookie_login_json
def tree(project_name):
	J = request.user.get_project(project_name)
	return json.dumps({'success': J.struct_to_dict()})



@app.route("/project/<project_name>/file/new", methods=['POST'])
@cookie_login_json
def new_file(project_name):
	J = request.user.get_project(project_name)
	data = request.json
	name = str(data['name']).strip()

	ext = os.path.splitext(name)[-1]
	if ext not in SUPPORTED_LANGUAGES:
		raise NotImplementedError("support for file type not implemented")

	res = J.new_file(data['path'], name)
	return json.dumps({'success': res})


@app.route("/project/<project_name>/file/save", methods=['POST'])
@cookie_login_json
def save_file(project_name):
	J = request.user.get_project(project_name)
	data = request.json
	res = J.save_file(data['path'], data['src'])
	return json.dumps({'success': res})


@app.route("/project/<project_name>/file/delete", methods=['POST'])
@cookie_login_json
def delete_file(project_name):
	J = request.user.get_project(project_name)
	data = request.json
	res = J.delete_file(data['path'])
	return json.dumps({'success': res})



@app.route("/project/<project_name>/folder/new", methods=['POST'])
@cookie_login_json
def new_folder(project_name):
	J = request.user.get_project(project_name)
	data = request.json
	name = str(data['name']).strip()

	res = J.new_folder(data['path'], name)
	return json.dumps({'success': res})




@app.route("/project/<project_name>/run", methods=['GET'])
@cookie_login_json
def run(project_name):
	msgs = []
	def _cb(msg):
		msgs.append(str(msg))

	with print_capture(_cb):
		J = request.user.get_project(project_name)
		J.run()

	return json.dumps({'success': ''.join(msgs)})





if __name__ == '__main__':
	app.run()
