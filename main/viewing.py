from flask import current_app
import json
import requests

# INDENT = 2


def get_response(query, client_id, oauth, broadcaster): 
	url = current_app.config['BASE_URL'] + query
	headers = {'Authorization': 'Bearer ' + oauth, 'Client-ID': client_id}
	params = (
		('login', broadcaster),
	)

	response = requests.get(url, headers=headers, params=params)
	return response
	
def get_video_info(client_id, oauth, broadcaster): 
	url = current_app.config['BASE_URL'] + 'users?login={0}'.format(broadcaster)
	headers = {'Authorization': 'Bearer ' + oauth, 'Client-ID': client_id}
	params = (
		('login', broadcaster),
	)
	
	response = requests.get(url, headers=headers, params=params)
	
	return response

def print_response(response):
	print(json.dumps(response.json(), indent=2))

def get_user_streams_query(user_login):
	return 'streams?user_login={0}'.format(user_login)

def get_user_query(user_login):
	return 'users?login={0}'.format(user_login)

def get_user_videos_query(user_id):
	return 'videos?user_id={0}&first=50'.format(user_id)

def get_games_query():
  return 'games/top'
