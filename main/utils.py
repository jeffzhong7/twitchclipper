from flask import (
	Blueprint, Flask, flash, g, redirect, render_template, request, url_for, send_from_directory, abort, current_app
)
from flask_ngrok import run_with_ngrok
from wtforms import Form, StringField, validators
from . import clipping
from . import viewing
import datetime
import json
import time
import os

bp = Blueprint('utils', __name__, url_prefix='/utils')


class InputForm(Form):
	client_id = StringField(validators=[validators.InputRequired()])
	oauth = StringField(validators=[validators.InputRequired()])
	broadcaster = StringField(validators=[validators.InputRequired()])

@bp.route('/')
def index():
	return render_template('base.html')
	
@bp.route('/clipping', methods=['GET', 'POST'])
def clipper():
	form = InputForm(request.form)
	if request.method == 'POST':
		client_id = form['client_id'].data
		oauth = form['oauth'].data
		broadcaster = form['broadcaster'].data
		
		try:
			if not os.path.isfile(current_app.config['CLIP_DIR'] + '/' + broadcaster + '-clips.zip'):
				broadcaster_id = clipping.verify(client_id, oauth, broadcaster)
				clips_data = clipping.collect(client_id, oauth, broadcaster_id)
				clipping.download(broadcaster, clips_data)
				
			return send_from_directory(current_app.config['CLIP_DIR'], filename=broadcaster + '-clips.zip', as_attachment=True)
		except FileNotFoundError:
			abort(404)
		
		return redirect(url_for('utils.clipping', broadcaster=broadcaster), code=302)
		
	return render_template('utils/clips.html', form=form)
	
@bp.route('/viewing', methods=['POST', 'GET'])
def viewer():
	form = InputForm(request.form)
	client_id = form['client_id'].data
	oauth = form['oauth'].data
	broadcaster = form['broadcaster'].data
	response = viewing.get_video_info(client_id, oauth, broadcaster)

	try:
		user_id = response.json()['data'][0]['id']
		img_url = response.json()['data'][0]['profile_image_url']
		
		user_videos_query = viewing.get_user_videos_query(user_id)
		videos_info = viewing.get_response(user_videos_query, client_id, oauth, broadcaster)

		viewing.print_response(videos_info)

		videos_info_json = videos_info.json()
		videos_info_json_data = videos_info_json['data']

		line_labels = []
		line_values = []
		title = broadcaster + '\'s Video Stats'

		for item in videos_info_json_data:
			if len(item['title']) == 0:
				line_labels.append('No Name')
			elif len(item['title']) > 20:
				line_labels.append(item['title'][:20] + '...')
			else:
				line_labels.append(item['title'])
			line_values.append(item['view_count'])

		return render_template('utils/line_chart.html', title=title, max=max(line_values) + 10, labels=line_labels, values=line_values, img_url=img_url)
	except:
		return render_template('utils/display.html', form=form)