from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory, abort, current_app
)
from . import clipper
import os

bp = Blueprint('utils', __name__, url_prefix='/utils')


@bp.route('/')
def index():
	return render_template('base.html')
	
@bp.route('/clipping', methods=['GET', 'POST'])
def clipping():
	if request.method == 'POST':
		client_id = request.form['client_id']
		oauth = request.form['oauth']
		broadcaster = request.form['broadcaster']
		
		try:
			if not os.path.isfile(current_app.config['CLIP_DIR'] + '/' + broadcaster + '-clips.zip'):
				broadcaster_id = clipper.verify(client_id, oauth, broadcaster)
				clips_data = clipper.collect(client_id, oauth, broadcaster_id)
				clipper.download(broadcaster, clips_data)
				
			return send_from_directory(current_app.config['CLIP_DIR'], filename=broadcaster + '-clips.zip', as_attachment=True)
		except FileNotFoundError:
			abort(404)
		
		return redirect(url_for('utils.clipping', broadcaster=broadcaster), code=302)
		
	return render_template('utils/clips.html')
	