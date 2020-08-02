from flask import Flask
from . import utils
from dotenv import load_dotenv
import os

# load dotenv in the base root
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)


def create_app(test_config=None):
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_pyfile('config.py')
	
	app.register_blueprint(utils.bp)
	app.add_url_rule('/', 'index', utils.index)
		
	return app;