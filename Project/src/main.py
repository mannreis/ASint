#!/usr/bin/env python3
from flask import Flask, Response, abort, make_response, render_template, request, jsonify, redirect, url_for, session
from itertools import chain
import db

from werkzeug.contrib.cache import SimpleCache

from functools import wraps

from random import randint
import requests
import json

import datetime

app = Flask(__name__)
app.config.from_pyfile('settings')

cache = SimpleCache()

db = db.Db()

with open("keys.json",'r') as f:
	APP = json.load(f)


'''with open("secret.jpg", 'rb') as f:
	app.secret_key = f.read()'''


APP['redirectURI'] = 'http://127.0.0.1:5000/'
APP['loginURI'] = 'https://fenix.tecnico.ulisboa.pt/oauth/userdialog?client_id='+str(APP['clientID'])+'&redirect_uri='+APP['redirectURI']

'''@app.after_request
def add_header(response):
	"""
	Add headers to both force latest IE rendering engine or Chrome Frame,
	and also to cache the rendered page for 10 minutes.
	"""
	response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
	response.headers['Cache-Control'] = 'public, max-age=0'
	return response'''

def validAdmin(username, password):
	return username == app.config['USER'] and password == app.config['PASS']

def admin(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		auth = request.authorization
		if not auth.username or not auth.password or not validAdmin(auth.username, auth.password):
			return Response('Credentials required!', 500, {'WWW-Authenticate': 'Basic realm="Login!"'})
		return f(*args, **kwargs)
	return wrapper


def validBot(user, key):
	if user != "bot":
		return False

	print(db.getBot(key))
	return (False if db.getBot(key) == None else True)

def bot(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		auth = request.authorization
		if not auth.username or not auth.password or not validBot(auth.username, auth.password):
			return Response('Valid key required!', 500, {'WWW-Authenticate': 'Basic realm="Login!"'})
		return f(*args, **kwargs)
	return wrapper


def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		user = session.get('username')
		if user is None:
			return redirect(APP['loginURI'])
		if user not in kwargs.values():
			return abort(401) #unauthorized
		return f(*args, **kwargs)
	return decorated_function

'''ADMIN ENDPOINTS'''
#Manage Buildings
@app.route('/API/admin/buildings/manage',methods=['PUT'])
@admin
def buildingsManagement():
	buildingList = []
	''' File containing buildings'''

	if request.is_json:
		buildingList = request.get_json()
	else:
		for i in request.form:
			for line in i.split('\n'):
				buildingList.add({"_id": ID, "name": name, "location": { "lat": lat, "lon": lon }})
	db.insertBuildings(buildingList)
	return "done"


@app.route('/API/admin/buildings',methods=['POST'])
@admin
def buildingsList():
	s = db.getBuildings()
	print(jsonify(s))
	return jsonify(s)

#Logged Users
@app.route('/API/admin/users/loggedin', methods=['POST'])
@admin
def listLoggedUsers():
	users = db.getAllLoggedUsers()
	for user in users:
		print(user)

#Logged Users In building
@app.route('/API/admin/buildings/<string:buildingID>/users', methods=['POST'])
@admin
def listUsersInBuilding(buildingID):
	return str(buildingID)

#History
@app.route('/API/admin/logs', methods=['POST'])
@admin
def history():
	return "hello"+request.url

#history by building
@app.route('/API/admin/building/<string:buildingID>/logs', methods=['POST'])
@admin
def historyByBuilding(buildingID, moves=True, messages=True):
	#return 'by building'
	if moves:
		#Movements in building
		buildingMoves = db.getBuildingMovements(buildingID)
	if messages:
		#Messages in building
		buildingMessages = db.getBuildingMessages(buildingID)

	if moves and messages:
		logs = sorted([l for l in chain(buildingMoves, buildingMessages)], key=lambda k: k['time'])
	elif moves and not messages:
		logs = buildingMoves
	elif messages and not moves:
		logs = buildingMessages

	return str(logs)

#history by user
@app.route('/API/admin/users/<string:istID>/logs', methods=['POST'])
@admin
def historyByUser(istID, moves=True, messages=True):
	#return 'by user'
	if moves:
		#User movements
		userMovements = getUserMovements(istID)
	if messages:
		#User messages
		userMessages = getUserMessages(istID)

	if moves and messages:
		logs = sorted([l for l in chain(userMovements, userMessages)], key=lambda k: k['time'])
	elif moves and not messages:
		logs = userMovements
	elif messages and not moves:
		logs = userMessages

	return str(logs)

#create new bot
@app.route('/API/admin/bot/create', methods=['PUT'])
@admin
def newBot():
	b = request.form['buildings'].split(',')
	r = db.insertBot(b)
	return jsonify({ 'key':r })


'''USER ENDPOINTS'''
@app.route('/API/login/', methods=['POST'])
@login_required
def fenixLogin():
	return jsonify({"istID":'2iwi2kd'})
	#User(1234)
	#fenixURL = 'https://fenix.tecnico.ulisboa.pt/oauth/userdialog?client_id='+str(FENIX_API['clientID'])+'&redirect_uri='+FENIX_API['redirectURI']
	#redirect(fenixURL)

#Send Message
@app.route('/API/users/<string:istID>/message', methods=['POST'])
@login_required
def sendMsg(istID):
	try:
		print(request.is_json)
		d = request.get_json()
		return str(db.insertMessage(istID, [*db.getUsersInRange(istID)], d.get('message'), d.get('location'), None))
	except:
		return abort(500)

#Set Range
@app.route('/API/users/<string:istID>/range/<int:newRange>',methods=['POST'])
@login_required
def setRange(istID, newRange):
	try:
		print(request.is_json)
		d = request.get_json()
		return str(db.updateUserRange(istID, newRange))
	except:
		return abort(500)

#Update user's location
@app.route('/API/users/<string:istID>/location',methods=['POST'])
@login_required
def updateLocation(istID):
	try:
		print(request.is_json)
		d = request.get_json()
		db.updateUserLocation(istID,d)
	except:
		return abort(500)
	return "ok"

#List users in range
@app.route('/API/users/<string:istID>/range', methods=['POST'])
@login_required
def usersInRange(istID):
	try:		
		users = db.getUsersInRange(istID)
		usersInBuilding = db.getUsersInSameBuilding(istID)
		if usersInBuilding != None:
			users.union(usersInBuilding)
		return jsonify({'users': "\n".join(users)})
	except:
		return abort(500)

#List messages received
@app.route('/API/users/<string:istID>/message/received', methods=['POST'])
@login_required
def received(istID):
	i = 0
	if request.is_json:
		i = int(request.get_json()['number'])
	return jsonify(db.getUserMessages(istID, lastIndex = i))

#Updates user's building
@app.route('/API/users/<string:istID>/building', methods=['POST'])
@login_required
def updateBuilding(istID):
	db.getUserBuilding(istID)
	return "ok"


'''BOTS ENDPOINTS'''
@app.route('/API/bots/<string:key>/message', methods=['POST'])
@bot
def dissipateMessage(key):
	if key != request.authorization.password:
		return Response('Endpoint not allowed!', 500)
	
	buildings = db.getBot(key)
	r = 0
	for buildingID in buildings:
		r = r + db.insertMessageInBuilding('Bot', request.data, buildingID)

	return 'Sending complete ('+str(r)+')'



#@app.route('/')
#def hello_world():
#	url='https://fenix.tecnico.ulisboa.pt/oauth/userdialog?client_id='+str(FENIX_API['clientID'])+'&redirect_uri='+FENIX_API['redirectURI']
#	return render_template("mainPage.html", url=url)

@app.route('/')
def hello_world():
	code = request.args.get('code')

	if code is None and not session.get('code'):
		return redirect(APP['loginURI'])

	elif code is not None and not session.get('token'):
		#cache.add('username',getUserInfo(),timeout = 5)
		session['code'] = code
		getUserInfo()
		return redirect('/')
	
	db.insertUser(session.get('username'), {'lat':0,'lon':0}, 10)
	resp = make_response(render_template("webApp.html", istID=session.get('username')))
	#resp.set_cookie('access_token', cache.get('access_token'))#
	return resp

@app.route('/testing/<string:istID>')
def testing(istID):
	session['username'] = istID
	db.insertUser(session.get('username'), {'lat':0,'lon':0}, 10)
	return render_template("webApp.html", istID=session.get('username'))


@app.route('/logout', methods = ['POST'])
@login_required
def logout():
	#db.removeUser(istID)
	print(session)	
	session.clear()
	print(session)
	return redirect('/login')
	#Here redirect to login page again
	#return render_template("webApp.html", istID)

@app.route('/login')
def log():
	return render_template("mainPage.html")


def getUserInfo():
    access_token_request_url = 'https://fenix.tecnico.ulisboa.pt/oauth/access_token'
    request_data = {'client_id': int(APP['clientID']), 'client_secret': APP['clientSecret'],
            'redirect_uri': APP['redirectURI'], 'code': session.get('code'), 'grant_type': 'authorization_code'}

    reqAccessToken = requests.post(access_token_request_url, data=request_data)

    token = reqAccessToken.json().get('access_token')
    session['token'] = token
    #cache.add('access_token', token, timeout=5)
    #print('access token in cache',cache.get('access_token'))


    request_info = requests.get('https://fenix.tecnico.ulisboa.pt/api/fenix/v1/person', params={'access_token': token})
    session['username'] = request_info.json().get('username')
    return


if __name__ == '__main__':
	app.run()