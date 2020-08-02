from enum import Enum
from flask import current_app
from numpy.core import unicode
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from time import strftime
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager
from zipfile import ZipFile
import argparse
import chromedriver_binary
import io
import json
import os
import re
import requests
import urllib.request
import sys
import time

indent = 2

def verify(client_id, oauth, broadcaster):
	response = requests.get('https://id.twitch.tv/oauth2/validate',
							headers={'Authorization': 'OAuth ' + oauth})
	# print(json.dumps(response.json(), indent=indent))
	
	if response.status_code != 200:
		print('Status {0}: error'.format(response.status_code))
		return
	else:
		print('Status {0}: verified client. '.format(response.status_code))

		response = requests.get('https://api.twitch.tv/helix/users',
								headers={'Authorization': 'Bearer ' + oauth, 'Client-ID': client_id},
								params={'login': broadcaster})
		data = response.json()['data'][0]
		print('Querying clips from {0} (id: {1})'.format(data['display_name'], data['id']))
		# print(json.dumps(response.json(), indent=indent))
		
		return data['id']
		
	
def collect(client_id, oauth, broadcaster_id):
	clips_data = {}
	response = requests.get('https://api.twitch.tv/helix/clips',
							headers={'Authorization': 'Bearer ' + oauth, 'Client-ID': client_id},
							params={'broadcaster_id': broadcaster_id, 'first': '100'})
	
	# print(json.dumps(response.json(), indent=indent))
	
	while response.json()['pagination']:
		clips = response.json()['data']
		for clip in clips:
			url = clip['thumbnail_url'].split('-preview')[0] + '.mp4'
			title = clip['title']
			
			cout = 1
			
			# handle duplicate clip titles
			if title in clips_data:
				newTitle = title + ' ({0})'.format(cout)
				while (newTitle in clips_data):
					cout = cout + 1
					newTitle = title + ' ({0})'.format(cout)
				title = newTitle
				
			clips_data[title] = url
		
		response = requests.get('https://api.twitch.tv/helix/clips',
							headers={'Authorization': 'Bearer ' + oauth, 'Client-ID': client_id},
							params={'broadcaster_id': broadcaster_id, 'first': '100', 'after': response.json()['pagination']['cursor']})
		
		# print(json.dumps(response.json(), indent=indent))
	
	# the last query will not produce a cursor
	clips = response.json()['data']
	for clip in clips:
		url = clip['thumbnail_url'].split('-preview')[0] + '.mp4'
		title = clip['title']
		
		cout = 1
		
		# handle duplicate clip titles
		if title in clips_data:
			newTitle = title + ' ({0})'.format(cout)
			while (newTitle in clips_data):
				cout = cout + 1
				newTitle = title + ' ({0})'.format(cout)
			title = newTitle
			
		clips_data[title] = url
		
	print('{0} clips found. '.format(len(clips_data)))
	return clips_data
	

def download(broadcaster, clips_data):
	# print(slugs)
	# os.makedirs('{0}-clips'.format(broadcaster), exist_ok=True)
	# guess i didn't need selenium 🤷‍ 
	"""
	options = webdriver.ChromeOptions()
	options.add_argument('--disable-gpu')
	options.add_argument('--mute-audio')
	options.add_argument('--log-level=3')
	options.add_argument('--disable-logging')
	driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
	"""
	
	os.makedirs(current_app.config['CLIP_DIR'], exist_ok=True)
	zipFile = ZipFile(current_app.config['CLIP_DIR'] + '/' + broadcaster + '-clips.zip', 'w')
	for title, url in tqdm(clips_data.items()):
		try:
			path_to_download_folder = str(os.path.join(Path.home(), 'Downloads'))
			
			"""
			driver.get(slugs[i])
			WebDriverWait(driver, 120).until(expected_conditions.visibility_of_element_located((By.TAG_NAME, 'video')))
			src = driver.find_element_by_tag_name('video').get_attribute('src')
			"""
			
			filename = re.sub('[^A-Za-z0-9()\\s]+', '', title)
			filename_ext = filename + '.mp4'

			bytes = io.BytesIO()
			clip_data = requests.get(url, allow_redirects=True).content
			
			bytes.write(clip_data)
			zipFile.writestr(filename_ext, bytes.getbuffer())
		except:
			# download failed :(
			continue
	
	# driver.quit()
	zipFile.close() 

def main():
	ap = argparse.ArgumentParser()
	ap.add_argument('-c', '--client', required=True,
					help="client id associated with your Twitch account")
	ap.add_argument('-o', '--oauth', required=True,
					help="oauth code associated with your Twitch account")
	ap.add_argument('-b', '--broadcaster', required=True,
					help="name of the Twitch channel to download from")
	args = vars(ap.parse_args())
	
	client_id = args['client']
	oauth = args['oauth']
	broadcaster = args['broadcaster']
	
	broadcaster_id = verify(client_id, oauth, broadcaster)
	clips_data = collect(client_id, oauth, broadcaster_id)
	download(broadcaster, clips_data)

if __name__ == '__main__':
	main()