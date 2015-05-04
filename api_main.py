# -*- coding: utf-8 -*
# Typical usage scenario:
# Request main page(get session id) -> Provide user id to parse friends from ->
# Request voting page -> Vote -> Request voting page ->...


from flask import Flask, render_template, \
	jsonify, request, make_response, redirect, \
	url_for
from db import Db
from vk import VK

app = Flask(__name__)
db = Db(host="ec2-54-163-227-94.compute-1.amazonaws.com",\
	database="d91m3map07tqmv",
	user="khpikwbwpupbry",\
	password="lpKpnxDUjlR0T7VOy5GeWw6bD5")
db.connect()

def parseVkId(str):
	# Try parsing without regexps for the sake of speed and simplicity
	indx = str.find('vk.com/')
	if indx < 0:
		raise ValueError('Cannot parse vk id from {}'.format(str))
	indx += len('vk.com/')
	return str[indx:]

class Girl:
	def __init__(self, id, pic):
		self.pic = pic
		self.id = id



class GirlPair:
	def __init__(self, girl1, girl2):
		self.girl1 = girl1
		self.girl2 = girl2
		
	@staticmethod
	def getRandomPair(session_id):
		id = db.getRandomIdPairForSession(session_id)
		#get pics from vk by returned ids
		pic = (VK.getPicUrlById(id[0]), VK.getPicUrlById(id[1]))
		girls = (Girl(id[0], pic[0]), Girl(id[1], pic[1]))
		return girls

#api method
@app.route("/getgirlpair")
def getGirlPair():
	randomPair = GirlPair.getRandomPair()
	return json(randomPair)

#api method
@app.route("/select/") #!!
def selectGirlInPair(girlBetter, girlWorse):
	db.connect()
	db.storeChosenGirl(girlBetter, girlWorse)
	db.disconnect()

#web-interface method
#@app.route("/")
#def getRoot():
	## Check if session_id is present in cookie
	#session_id = request.cookies.get('session_id')
	#vk_id = ''
	#if session_id is None:
		##no session id found. Start new session
		#session_id = db.createSession()
	#else:
		## Check if such session id is in db
		#stored_session_id, stored_vk_id = db.getSessionParams(session_id)
		#if stored_session_id is None:
			#session_id = db.createSession()
		#else:
			#vk_id = stored_vk_id
	
	#resp = make_response(render_template('mainpage.html', vk_id=vk_id))
	#resp.set_cookie('session_id', str(session_id))
	#return resp

##web-interface method
#@app.route("/loadfriends/")
#def loadfriends(vk_id=None):
	#session_id = request.cookies.get('session_id')
	#try:
		#vk_id = parseVkId(request.args.get('vk_id'))
		#id = VK.getIdByShortName(vk_id)
	#except ValueError:
		#return redirect(url_for('getRoot'))
	#stored_vk_id = db.getStoredVkIdForSession(session_id)
	#if vk_id is None:
		## No vk_id provided. Perhaps we already have some vk_id recorded
		## for this session
		#vk_id = stored_vk_id
		#id = VK.getIdByShortName(vk_id)
		#if vk_id is None:
			## Still no vk_id? Well, let's ask for it again
			#return redirect(url_for('getRoot'))
	#elif id != stored_vk_id:
		## In this case, we treat stored vk_id as deprecated and update it
		#db.updateStoredVkIdForSession(session_id, id)

	#friends = VK.getFriendsIds(id)
	#db.cleanupUsersForSession(session_id)
	#db.storeUsersForSession(session_id, friends)
	#return redirect(url_for('vote'))

##web-interface method
#@app.route("/vote/")
#def vote():
	#session_id = request.cookies.get('session_id')
	#girl1, girl2 = GirlPair.getRandomPair(session_id)
	#resp = make_response(render_template('votepage.html', \
		#girl1=girl1, girl2=girl2))
	#return resp

##web-interface method
#@app.route("/voteres/")
#def voteRes():
	#print(request.args)
	#girls = {girl_id for key, girl_id in request.args.items() \
		#if key in ('girl1_id', 'girl2_id')}
	#girlBetter = request.args.get('votegirl')
	#girlWorse = list(girls - set((girlBetter,)))[0]
	#db.storeChosenGirl(girlBetter, girlWorse)
	#return redirect(url_for('vote'))


# New web-interface method
@app.route("/")
def getMain():
	sessionId = getSessionId()
	
	try:
		vkId = parseVkId(request.args.get('vk_id'))
		vkId = VK.getIdByShortName(vkId)
	except ValueError:
		return redirect(url_for('getMain'))
		
	if vkId is None and vkIdStored is None:
		# No vk_id has been provided yet. Wait for it
		resp = make_response(render_template('index.html', vk_id=vkId))
		resp.set_cookie('session_id', str(sessionId))
		return resp
	
	if vkId is None and vkIdStored is not None:
		vkId = vkIdStored
	elif vkId != vkIdStored:
		db.cleanupUsersForSession(sessionId)
		db.updateStoredVkIdForSession(sessionId, vk_id)
	
	# На этом этапе мы уже знаем, что ид у нас есть, но мы не знаем,
	# грузили ли мы уже его подруг или нет. Надо проверить
	
	if db.areFriendsLoaded(sessionId) == False:
		friends = VK.getFriendsIds(vkId)
		db.cleanupUsersForSession(sessionId)
		db.storeUsersForSession(sessionId, friends)
	
	# Теперь мы уверены, что инфа по подругам в базе. Достаем рандомную
	# пару и грузим ссылки на их аватарки из вконтакта
	girl1, girl2 = GirlPair.getRandomPair(sessionId)
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
	sessionId = getSessionId()
	sessionIdStored, vkIdStored, girlLeftStored, girlRightStored = \
		db.getSessionParams(session_id)
	if girlLeftStored is not None and girlRightStored is not None:
		db.storeChosenGirl(girlLeftStored, girlRightStored)
		
	return redirect(url_for('getMain'))

@app.route("/vote/right/")
def voteRight():
	sessionId = getSessionId()
	sessionIdStored, vkIdStored, girlLeftStored, girlRightStored = \
		db.getSessionParams(session_id)
	if girlLeftStored is not None and girlRightStored is not None:
		db.storeChosenGirl(girlRightStored, girlLeftStored)
		
	return redirect(url_for('getMain'))

@app.route("/vote/skip/")
def voteSkip():
	sessionId = getSessionId()
	
	return redirect(url_for('getMain'))

def getSessionId():
	sessionId = request.cookies.get('session_id')
	if session_id is None:
		#no session id found. Start new session
		session_id = db.createSession()
	# Check if such session id is in db
	sessionIdStored, vkIdStored, girlLeftStored, girlRightStored = \
		db.getSessionParams(session_id)
	if sessionIdStored is None:
		sessionId = db.createSession()
	return sessionId

if __name__ == '__main__':
	app.run(debug=True)
