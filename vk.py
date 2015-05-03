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
		return res.json()['response'][0]['id']
	
	@staticmethod
	def getFriendsIds(id):
		offset = 0
		query = "http://api.vk.com/method/friends.get?user_id={}&v=5.30&fields=sex".format(id)
		res = requests.get(query)
		users = [item['id'] for item in res.json()['response']['items'] \
			if item['sex']==1]
		return users
