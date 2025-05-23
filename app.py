from flask import Flask, jsonify, request, render_template, make_response, session
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_cors import CORS
from flask_session import Session
import os
from server.controllers.user_manager import User

from server.views import blog

# A configuration for allowing testing features in `HTTP` that are only available for `HTTPS`
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Flask Server instance
app = Flask(__name__, static_url_path='/static', static_folder='client/static', template_folder='client/templates')
CORS(app) # For Cross Origin Resource Sharing
app.secret_key = 'test_key2' # TODO Temporarily, a fixed key is used to keep the sessions, testing purpose

# Session
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
Session(app)

# Blutprint
app.register_blueprint(blog.blog, url_prefix='/blog')

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'


# A hook to return an instance of User class, using the user_id included in the session information
@login_manager.user_loader
def load_user(user_id: str):
    return User.find_user(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Unauthorized'}), 401


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
