import os
import json
import traceback
from flask import Flask, send_file, request

from capture import print_capture
from project import Project

CWD = os.path.dirname(os.path.abspath(__file__))



app = Flask(__name__)

TEST_USER = 'sgop'


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





@app.route("/", methods=['GET'])
def home():
	return send_file(os.path.join(CWD, 'web', 'index.html'))


@app.route("/static/<folder>/<filename>", methods=['GET'])
def static_files(folder, filename):
	return send_file(os.path.join(CWD, 'web', folder, filename))


# Project API
@app.route("/project/<project_name>", methods=['GET'])
def open_project(project_name):
	Project(project_name, user_name=TEST_USER) # basic file structure init
	return openHTML(os.path.join(CWD, 'web', 'project.html'), project_name=project_name)


@app.route("/project/<project_name>/tree", methods=['GET'])
def tree(project_name):
	J = Project(project_name, user_name=TEST_USER)
	return json.dumps({'success': J.struct_to_dict()})


@app.route("/project/<project_name>/file/save", methods=['POST'])
def save_file(project_name):
	J = Project(project_name, user_name=TEST_USER)
	data = request.json
	res = J.save_file(data['path'], data['src'])
	return json.dumps({'success': res})


@app.route("/project/<project_name>/file/delete", methods=['POST'])
def delete_file(project_name):
	J = Project(project_name, user_name=TEST_USER)
	data = request.json
	res = J.delete_file(data['path'])
	return json.dumps({'success': res})


@app.route("/project/<project_name>/file/new", methods=['POST'])
def new_file(project_name):
	J = Project(project_name, user_name=TEST_USER)
	data = request.json
	name = str(data['name']).strip()
	if not name.endswith(".py"):
		raise NotImplementedError("support for file type not implemented")

	res = J.new_file(data['path'], name)
	return json.dumps({'success': res})


@app.route("/project/<project_name>/run", methods=['GET'])
def run(project_name):
	msgs = []
	def _cb(msg):
		msgs.append(str(msg))

	with print_capture(_cb):
		try:
			J = Project(project_name, user_name=TEST_USER)
			print(J.run())
		except:
			traceback.print_exc()
	return json.dumps({'success': ''.join(msgs)})





if __name__ == '__main__':
	app.run()
