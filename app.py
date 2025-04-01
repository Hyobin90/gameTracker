from flask import Flask, jsonify, request, render_template, make_response, session
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_cors import CORS
import os

# A configuration for allowing testing features in `HTTP` that are only available for `HTTPS`
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Flask Server instance
app = Flask(__name__, static_url_path='/client/static')
CORS(app) # For Cross Origin Resource Sharing
app.secret_key = 'test_key' # TODO Temporarily, a fixed key is used to keep the sessions, testing purpose

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'

@login_manager.user_loader
def load_user(user_id: str):
    