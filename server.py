import os
import json
import traceback
from flask import Flask, send_file, request

from capture import print_capture
from jobs import Job

CWD = os.path.dirname(os.path.abspath(__file__))



app = Flask(__name__)


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
@app.route("/<user>/<job>", methods=['GET'])
def open_project(user, job):
	Job(job, user) # basic file structure init
	return openHTML(os.path.join(CWD, 'web', 'project.html'), user=user, job=job)


@app.route("/<user>/<job>/tree", methods=['GET'])
def tree(user, job):
	J = Job(job, user)
	return json.dumps({'success': J.struct_to_dict()})


@app.route("/<user>/<job>/file/save", methods=['POST'])
def save_file(user, job):
	J = Job(job, user)
	data = request.json
	res = J.save_file(data['path'], data['src'])
	return json.dumps({'success': res})


@app.route("/<user>/<job>/file/delete", methods=['POST'])
def delete_file(user, job):
	J = Job(job, user)
	data = request.json
	res = J.delete_file(data['path'])
	return json.dumps({'success': res})


@app.route("/<user>/<job>/file/new", methods=['POST'])
def new_file(user, job):
	J = Job(job, user)
	data = request.json
	name = str(data['name']).strip()
	if not name.endswith(".py"):
		raise NotImplementedError("support for file type not implemented")

	res = J.new_file(data['path'], name)
	return json.dumps({'success': res})


@app.route("/<user>/<job>/run", methods=['GET'])
def run(user, job):
	msgs = []
	def _cb(msg):
		msgs.append(str(msg))

	with print_capture(_cb):
		try:
			J = Job(job, user)
			print(J.run())
		except:
			traceback.print_exc()
	return json.dumps({'success': ''.join(msgs)})





if __name__ == '__main__':
	app.run()
