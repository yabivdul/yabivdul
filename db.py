import psycopg2

class Db:
	def __init__(self, **connAgrs):
		self.connArgs = connAgrs
		self.cursor = None
	
	def connect(self):
		if self.cursor is None:
			self.__con = psycopg2.connect(**self.connArgs)
			self.cursor = self.__con.cursor()
	
	def getMaxSessionId(self):
		query = """
		select max(session_id) from session
		"""
		self.cursor.execute(query)
		max_id = self.cursor.fetchone()[0]
		if max_id is None:
			#no sessions yet
			max_id = 0
		
		return max_id
		
	def createSession(self):
		newSessionId = self.getMaxSessionId()+1
		query = """
		insert into session values (%s)
		"""
		self.cursor.execute(query, (newSessionId,))
		self.__con.commit()
		return newSessionId
	
	def getSessionParams(self, session_id):
		query = """
		select session_id, vk_id, girl_left_id, girl_right_id from session where session_id=%s
		"""
		self.cursor.execute(query, (session_id))
		res = self.cursor.fetchone()
		if res is None:
			return (None, None, None, None)
		else:
			return (res[0], res[1], res[2], res[3])
	
	def getStoredVkIdForSession(self, session_id):
		query = """
		select vk_id from session where session_id=%s
		"""
		self.cursor.execute(query, (session_id))
		res = self.cursor.fetchone()
		if res is None:
			return res
		else:
			return res[0]
	
	def updateStoredVkIdForSession(self, session_id, vk_id):
		query = """
		update session set vk_id = %s where session_id=%s
		"""
		self.cursor.execute(query, (vk_id, session_id))
		self.__con.commit()
	
	def getRandomIdPairForSession(self, session_id):
		query = """
		select user_id from girls where session_id=%s order by random() limit 2;
		"""
		self.cursor.execute(query, (session_id,))
		data = self.cursor.fetchall()
		data = [data_piece[0] for data_piece in data]
		return data
	
	def storeChosenGirl(self, girlBetterId, girlWorseId):
		# first check if such pair already exists
		query = """
		select counts from girl_pair_votes where id_better=%s and id_worse=%s
		"""
		self.cursor.execute(query,(girlBetterId, girlWorseId))
		counts = self.cursor.fetchone()
		if counts is None:
			#no such pair in db yet
			counts = 0
			query = """
			insert into girl_pair_votes values (%s, %s, %s)
			"""
			self.cursor.execute(query, (girlBetterId, girlWorseId, counts))
		else:
			counts = counts[0]
		
		#increment current pair counts and update it in db
		counts += 1
		query = """
		update girl_pair_votes set counts=%s where id_better=%s and id_worse=%s
		"""
		self.cursor.execute(query, (counts, girlBetterId, girlWorseId))
		self.__con.commit()
	
	def storeUsersForSession(self, session_id, users):
		query = b"""
		insert into girls (user_id, session_id)
		values 
		"""
		data = b','.join(self.cursor.mogrify(
			'(%s,%s)',(data_chunk, session_id)
		) for data_chunk in users)
		query += data
		self.cursor.execute(query)
		self.__con.commit()
	
	def areFriendsLoaded(self, sessionId):
		query = """
		select count(*) from girls where session_id=%s
		"""
		self.cursor.execute(query, (sessionId,))
		count = self.cursor.fetchone()
		if count is None or count[0] < 1:
			return False
		else:
			return True
	
	def updateStoredGirlsForSession(self, sessionId, girlLeftId, girlRightId):
		query = """
		update session set girl_left_id = %s, girl_right_id = %s where
		session_id = %s
		"""
		self.cursor.execute(query, (girlLeftId, girlRightId, sessionId))
		self.__con.commit()
	
	def cleanupUsersForSession(self, session_id):
		query = """
		delete from girls where session_id=%s
		"""
		self.cursor.execute(query, (session_id,))
		self.__con.commit()
	
	def disconnect(self):
		#!! not implemented yet
		pass
