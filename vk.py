import requests

class VK:
	@staticmethod
	def getPicUrlById(id):
		id = VK.getIdByShortName(id)
		query = "http://api.vk.com/method/users.get?user_id={}&v=5.30&fields=photo_max_orig".format(id)
		
		res = requests.get(query)
		#if res.status_code != '200':
		#	return None
		
		pic_url = res.json()['response'][0]['photo_max_orig']
		return pic_url
	
	@staticmethod
	def getIdByShortName(name):
		query = "http://api.vk.com/method/users.get?user_ids={}&v=5.30".format(name)
		res = requests.get(query)
		response = res.json()['response']
		if len(response) == 0:
			raise ValueError("Cannot find user with name {}".format(name))
		id = response[0].get('id', None)
		if id is None:
			raise ValueError("Cannot find user with name {}".format(name))
		return id
	
	@staticmethod
	def getFriendsIds(id):
		# !!TODO: check if returned list could exceed 5k and get remaining
		# friends if it does (vk limit on returning max 5000 recs)
		offset = 0
		query = "http://api.vk.com/method/friends.get?user_id={}&v=5.30&fields=sex".format(id)
		res = requests.get(query)
		users = [item['id'] for item in res.json()['response']['items'] \
			if item.get('sex')==1 and item.get('deactivated') is None \
			and item.get('hidden') != 1]
		return users
