# -*- coding: utf-8 -*
# Typical usage scenario:
# Request main page(get session id) -> Provide user id to parse friends from ->
# Request voting page -> Vote -> Request voting page ->...

# Url map:
# /
# /api/vote/		(parameters: id_voted)
# /api/rating/		(parameters: lower_rank, higher_rank) 
# /api/get_random_pair/
# /vote/left/		DEPRECATED
# /vote/right/		DEPRECATED

from flask import Flask, render_template, \
	jsonify, request, make_response, redirect, \
	url_for, g, json
from db import Db
from vk import VK
from credentials import dbCredentials

app = Flask(__name__)
db = Db(**dbCredentials)

@app.before_request
def dbConnect():
	db.connect()
	g.db = db

@app.teardown_request
def dbCleanup(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.disconnect()

def parseVkId(str):
	parsedId = None
	# Try parsing without regexps for the sake of speed and simplicity
	if str is None or len(str) == 0:
		raise ValueError('Cannot parse vk id from {}'.format(str))
	indx = str.find('vk.com/')
	if indx < 0:
		# Maybe we got an already parsed vk_id?
		try:
			parsedId = int(str)
		except ValueError:
			# Nope, we didnt. Report error
			raise ValueError('Cannot parse vk id from {}'.format(str))
	else:
		indx += len('vk.com/')
		parsedId = str[indx:]
	
	# Now we need to make sure that user with such id exists
	id = VK.getIdByShortName(parsedId)
	return id

class Girl:
	def __init__(self, id, pic):
		self.pic = pic
		self.id = id



class GirlPair:
	def __init__(self, girl1, girl2):
		self.girl1 = girl1
		self.girl2 = girl2
		
	@staticmethod
	def getRandomPair(session_id, db):
		id = db.getRandomIdPairForSession(session_id)
		#get pics from vk by returned ids
		pic = (VK.getPicUrlById(id[0]), VK.getPicUrlById(id[1]))
		girls = (Girl(id[0], pic[0]), Girl(id[1], pic[1]))
		return girls


# web-interface method
@app.route("/")
def getMain():
	db = getattr(g, 'db', None)
	sessionId, vkIdStored, girlLeftStored, girlRightStored = getSessionParams(db)
	
	vkIdRaw = request.args.get('vk_id')
	
	if vkIdRaw is None and vkIdStored is None:
		# No vk_id has been provided yet. Wait for it
		resp = make_response(render_template('index.html'))
		resp.set_cookie('session_id', str(sessionId))
		return resp
	
	vkId = None
	try:
		vkId = parseVkId(vkIdRaw)
		vkId = VK.getIdByShortName(vkId)
	except ValueError:
		if vkIdStored is None:
			return redirect(url_for('getMain'))
	
	if vkId is None and vkIdStored is not None:
		vkId = vkIdStored
	elif vkId != vkIdStored:
		db.cleanupUsersForSession(sessionId)
		db.updateStoredVkIdForSession(sessionId, vkId)
	
	# На этом этапе мы уже знаем, что ид у нас есть, но мы не знаем,
	# грузили ли мы уже его подруг или нет. Надо проверить
	
	if db.areFriendsLoaded(sessionId) == False:
		friends = VK.getFriendsIds(vkId)
		db.cleanupUsersForSession(sessionId)
		db.storeUsersForSession(sessionId, friends)
	
	# Теперь мы уверены, что инфа по подругам в базе. Достаем рандомную
	# пару и грузим ссылки на их аватарки из вконтакта
	girl1, girl2 = GirlPair.getRandomPair(sessionId, db)
	# Апдейтим запись в сессии новыми айдишниками девочек
	db.updateStoredGirlsForSession(sessionId, girl1.id, girl2.id)
	
	# Теперь у нас есть фотки девочек. Рендерим шаблон главной,
	# вставляем в него фотки и отдаем
	resp = make_response(render_template('index.html',\
		vk_id=vkId, girl1=girl1, girl2=girl2))
	resp.set_cookie('session_id', str(sessionId))
	return resp

# Vote for left girl and redirect to index
@app.route("/vote/left/")
def voteLeft():
	db = getattr(g, 'db', None)
	sessionId, vkIdStored, girlLeftStored, girlRightStored = getSessionParams(db)

	if girlLeftStored is not None and girlRightStored is not None:
		db.storeChosenGirl(girlLeftStored, girlRightStored)
		
	return redirect(url_for('getMain'))

@app.route("/vote/right/")
def voteRight():
	db = getattr(g, 'db', None)
	sessionId, vkIdStored, girlLeftStored, girlRightStored = getSessionParams(db)
	if girlLeftStored is not None and girlRightStored is not None:
		db.storeChosenGirl(girlRightStored, girlLeftStored)
		
	return redirect(url_for('getMain'))

@app.route("/vote/skip/")
def voteSkip():
	db = getattr(g, 'db', None)
	sessionId, vkIdStored, girlLeftStored, girlRightStored = getSessionParams(db)
	
	return redirect(url_for('getMain'))

#api method
@app.route("/api/get_random_pair", methods=['GET'])
def getGirlPair():
	db = getattr(g, 'db', None)
	#!! TODO: add error processing here
	randomPair = GirlPair.getRandomPair(db)
	return json(randomPair)

@app.route("/api/vote/", methods=['GET'])
def vote():
	db = getattr(g, 'db', None)
	sessionId, vkIdStored, girlLeftStored, girlRightStored = getSessionParams(db)
	
	try:
		idVoted = int(request.args.get('id_voted'))
	except (TypeError):
		return json.jsonify(
			error=True,
			error_description='Cannot resolve vk_id'
		)
	idNonVoted = set((girlLeftStored, girlRightStored)) - set((idVoted,))
	
	if girlLeftStored is not None and girlRightStored is not None:
		db.storeChosenGirl(girlBetterId=idVoted, girlWorseId=idNonVoted)
		return json.jsonify(
			id_voted=idVoted,
			id_non_voted=idNonVoted
		)

@app.route("/api/rating/", methods=['GET'])
def getRatingApi():
	db = getattr(g, 'db', None)
	try:
		lowerRank = int(request.args.get('lower_rank'))
		higherRank = int(request.args.get('higher_rank'))
		assert lowerRank <= higherRank
		assert lowerRank >= 0
		assert higherRank - lowerRank < 100
	except (TypeError, AssertionError):
		return json.jsonify(
			ranks=[],
			error=True,
			error_description='Invalid parameters for request'
		)
	return json.jsonify(ranks=db.getRating(lowerRank, higherRank))
	

def getSessionParams(db):
	sessionId = request.cookies.get('session_id')
	if sessionId is None:
		#no session id found. Start new session
		sessionId = db.createSession()
	# Check if such session id is in db
	sessionIdStored, vkIdStored, girlLeftStored, girlRightStored = \
		db.getSessionParams(sessionId)
	if sessionIdStored is None:
		sessionId = db.createSession()
	return (sessionId, vkIdStored, girlLeftStored, girlRightStored)

if __name__ == '__main__':
	app.run()
