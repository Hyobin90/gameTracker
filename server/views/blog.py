import datetime
from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_user
from server.controllers.user_manager import User

blog = Blueprint('blog', __name__) # TODO check if the relative path works well


@blog.route('/')
def load_main_page():
    return render_template('index.html')


@blog.route('/sign_up', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_email = request.form.get('user_email')
        password = request.form.get('password')

        try:
            new_user = User.create_user(user_email, password)    # Create a user
            login_user(new_user, remember=True, duration=datetime.timedelta(days=30))   # Create a session (the new user is logged in right away)
            return redirect(url_for('/blog'))
        except RuntimeError as e:
            return render_template('index.html', error=e)

