import urllib.request
import sys
import requests
import feedparser
import wget
import os
import platform
import eyed3
import math
import time
from pathlib import Path, PureWindowsPath
from PySide2 import QtCore, QtWidgets, QtGui
from pygame import mixer

class MyWidget(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		self.content = ' ' # Raw website information
		self.site_size = 0 # Size in Bytes
		self.parsed_site = '' # Parsed website
		self.file_list = []
		self.mp3 = ' ' # mp3 url
		self.mp3_name = ' ' # name of mp3
		self.mp3_index = 0 # mp3 index
		self.parsed_site = ' '
		self.mp3_file_name = ' '
		self.mp3_feed = ' '
		self.paused = False
		self.total = 0

		self.site = QtWidgets.QLineEdit()
		self.save_button = QtWidgets.QPushButton("Save Feed")
		self.load_button = QtWidgets.QPushButton("Load Feed List")
		self.download_button = QtWidgets.QPushButton("Download")
		self.play_button = QtWidgets.QPushButton("play")
		self.pause_button = QtWidgets.QPushButton("pause")
		self.stop_button = QtWidgets.QPushButton("stop")
		self.unpause_button =  QtWidgets.QPushButton("unpause")
		self.text = QtWidgets.QLabel(self.site)
		self.play_saved_mp3 = QtWidgets.QPushButton("play saved mp3")
		self.mp3_list = QtWidgets.QListWidget()
		self.saved_feed_list = QtWidgets.QListWidget()

		#Layout 
		self.layout = QtWidgets.QVBoxLayout()
		self.layout.addWidget(self.site)
		self.layout.addWidget(self.text, alignment=QtCore.Qt.AlignLeft)
		self.layout.addWidget(self.download_button, alignment=QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.save_button, alignment=QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.load_button, alignment=QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.play_saved_mp3, alignment=QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.mp3_list)
		self.layout.addWidget(self.saved_feed_list)
		self.saved_feed_list.hide()
		self.mp3_list.hide()

		#Dialog Layout
		self.setLayout(self.layout)
		self.test = 'testing'
		
		#button click
		self.download_button.clicked.connect(self.run_stuff)
		self.save_button.clicked.connect(self.save_feed)
		self.load_button.clicked.connect(self.load_saved_feeds)
		self.mp3_list.itemDoubleClicked.connect(self.download_feed)
		self.saved_feed_list.itemDoubleClicked.connect(self.list_saved_feeds)

	def list_saved_feeds(self):
		self.mp3_list.hide()
		self.saved_feed_list.show()
		self.option = self.saved_feed_list.currentRow()

		feed_path, config_path = assign_paths()

		with open(config_path + 'config.txt', 'r') as f:
			s = f.readlines()
		f.close()
		for x, i in enumerate(s):
			print('%s: %s' % (x,i),end='')
			self.saved_feed_list.addItem(str(i))

		for x, i in enumerate(s):
			if self.option == x:
				self.site.setText(i)
				print('%s: %s' % (x,i),end='')
		self.run_stuff()

	def alert_message(self, message_str, text_str):
		self.msg_box = QtWidgets.QMessageBox()
		self.msg_box.setText(message_str)
		self.text.setText(text_str)
		self.msg_box.exec()
		self.text.setText(' ')

	def save_feed(self):
		feed_path, config_path = assign_paths()
		s = str(self.site.text())
		with open(config_path + 'config.txt', 'a+') as f:
			f.write(s + '\n')
		f.close()
		self.alert_message('Feed Saved!','Saved!')

	def load_saved_feeds(self):
		self.mp3_list.hide()
		self.saved_feed_list.show()
		feed_path, config_path = assign_paths()

		with open(config_path + 'config.txt', 'r') as f:
			s = f.readlines()
		f.close()
		for x, i in enumerate(s):
			print('%s: %s' % (x,i),end='')
			self.saved_feed_list.addItem(str(i))

	def play_mp3(self):
		mixer.music.play()

	def play_audio(self,feed_path):
		mixer.init()
		mixer.music.load(feed_path + self.parsed_site.entries[self.mp3_index].author + '\\' + self.mp3_file_name)
		
		self.mp3_time = self.mp3_time / 60
		self.mp3_seconds, self.mp3_minutes = math.modf(self.mp3_time)
		self.mp3_seconds = round(self.mp3_seconds, 2)
		
		self.mp3_minutes = str(self.mp3_minutes)[:-1]
		self.mp3_seconds = str(self.mp3_seconds)[2:]

		#print('seconds: %s\n Minutes: %s' % (self.mp3_seconds, self.mp3_minutes))

		#time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
		#self.text.setText('time left:' +  str(self.mp3_minutes) + str(self.mp3_seconds))
		self.layout.addWidget(self.play_button)
		self.play_button.clicked.connect(self.play_mp3)

		self.layout.addWidget(self.pause_button)
		self.pause_button.clicked.connect(self.check_if_paused)
		
		self.layout.addWidget(self.stop_button)
		self.stop_button.clicked.connect(mixer.music.stop)


	def check_if_paused(self):
			if self.paused:
				self.paused = False
				return mixer.music.unpause()	
			else:
				self.paused = True
				return mixer.music.pause()
				
			
	def save_meta_data(self, feed_path):
		audiofile = eyed3.load(feed_path + self.parsed_site.entries[self.mp3_index].author + '\\' + self.mp3_file_name)
		audiofile.tag.artist = self.parsed_site.entries[self.mp3_index].author
		audiofile.tag.title = self.parsed_site.entries[self.mp3_index].title
		audiofile.tag.album_artist = self.parsed_site.entries[self.mp3_index].author
		audiofile.tag.track_num = self.mp3_index

		self.mp3_time = round(audiofile.info.time_secs)
		print(self.mp3_time)
		audiofile.tag.save()
		
	# byte size of website
	def download_feed(self,flag):

		feed_path, config_path = assign_paths()
		self.mp3_index = self.mp3_list.currentRow()
		
		self.mp3_feed = self.parsed_site.entries[self.mp3_index].links[1].href

		# Names mp3 file with title of podcast episode
		# as well as replace any spaces with underscores
		self.mp3_name = self.parsed_site.entries[self.mp3_index].title + '.mp3'

		self.file_destination = feed_path + self.mp3_name
		self.mp3_name = self.mp3_name.replace(' ', '_')
		self.parsed_site.entries[self.mp3_index].author = self.parsed_site.entries[self.mp3_index].author.replace(' ', '_')
		os.system('mkdir ' + feed_path + self.parsed_site.entries[self.mp3_index].author + '\\' )
		wget.download(self.mp3_feed, feed_path + self.parsed_site.entries[self.mp3_index].author + '\\')
		test = feed_path + self.parsed_site.entries[self.mp3_index].author + '\\'
		
		path_on_windows = '.'
		file_list = []
		root_dir = '.'
		print('')

		for dir_name, sub_dir_list, fileList in os.walk(root_dir):	
		
			#if(dir_name == path_on_windows):
			if dir_name == '.\\feeds\\' + self.parsed_site.entries[self.mp3_index].author:
				#'.\\feeds\\Lex_Fridman':
				print("dir_name: %s" % dir_name)
				for fname in fileList:
					print("fname:%s" % fname)
					file_list.append(fname)
					print("subdir: %s" % sub_dir_list)
							#print(sub_dir_list) 
		
		for n in file_list:
			print(n)
			if n in self.mp3_feed:
				print("found! site:%s file_name: %s" % (self.mp3_feed,n))
				self.mp3_file_name = n

		self.save_meta_data(feed_path)
		self.play_audio(feed_path)


	def get_site_size(self):
		# Gets Byte size of website
		response = requests.get(self.site.text())
		self.site_size = len(response.content)
		self.text.setText('Site Byte Size: %d' % (self.site_size))
	
	def print_info(self):
		#list = QtCore.QStringListModel.stringList(self.pased_site.entries.title)
		#set_list = QtCore.QStringListModel.setStringList(self.parsed_site.entries)
		self.parsed_site.entries.reverse()
		for x in range(0,len(self.parsed_site.entries)):
			#print(("%d: %s") % (x , self.parsed_site.entries[x].title))
			self.mp3_list.addItem(str(self.parsed_site.entries[x].title))

	def download_site(self):
		with urllib.request.urlopen(self.site.text()) as f:
			self.content = f.read(self.site_size).decode('utf-8')
		self.parsed_site = feedparser.parse(self.site.text())
		print(self.site.text())

	def run_stuff(self):
			self.saved_feed_list.hide()
			self.mp3_list.show()
			assign_paths()
			self.get_site_size()
			self.download_site()
			self.print_info()

	def get_file_list(self):
		unix_path = './feeds'
		path_on_windows = '.'
		root_dir = '.'
		print('')

		for dir_name, sub_dir_list, fileList in os.walk(root_dir):
			if(platform.system() == 'Linux' or platform.system() == 'Darwin'):
			# print(dir_name)
				if(dir_name == unix_path):
					for fname in fileList:
						print("\t%s" % fname)
						file_list.append(fname)	
						print(self.file_list)	
			elif platform.system() == 'Windows':
				# print(dir_name)
				if(dir_name == path_on_windows):
					for fname in fileList:
						print("\t%s" % fname)
						self.file_list.append(fname) 
			else:
				print("os not recognized")

def assign_paths():
	unix_feed_path = './feeds/'
	unix_config_path = './config/'
	windows_feed_path = '.\\feeds\\'
	windows_config_path = '.\\config\\'

	if(platform.system() == 'Linux' or platform.system() == 'Darwin'):
		feed_path = unix_feed_path
		config_path = unix_config_path
	elif platform.system() == 'Windows':
		feed_path = windows_feed_path
		config_path = windows_config_path
	else:
		print("os not recognized")
	return feed_path, config_path

if __name__ == "__main__":

	app = QtWidgets.QApplication([])

	widget = MyWidget()
	widget.resize(800, 600)
	widget.show()
	
	sys.exit(app.exec_())