import bcrypt
import datetime
from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import current_user, login_user, logout_user
from server.controllers.user_manager import User
from server.models.mongodb import connect_mongodb

blog = Blueprint('blog', __name__) # TODO check if the relative path works well


@blog.route('/')
def load_main_page():
    if current_user.is_authenticated:
        return render_template('index.html', user_email=current_user.user_email)
    else:
        return render_template('index.html')


@blog.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    """Creates a new user with the provided email and password."""
    if request.method == 'POST':
        user_email = request.form.get('user_email')
        password = request.form.get('password')

        try:
            new_user = User.create_user(user_email, password)    # Create a user
            login_user(new_user, remember=True, duration=datetime.timedelta(days=30))   # Create a session (the new user is logged in right away)
            return redirect(url_for('.load_main_page'))
        except RuntimeError as e:
            return render_template('index.html', error=str(e)), 400
        

@blog.route('/log_in', methods=['GET', 'POST'])
def log_in():
    """Logs in a user with the provided email and password."""
    if request.method == 'POST':
        user_email = request.form.get('user_email')
        entered_password = request.form.get('password')

        user_db = connect_mongodb('users')
        user_collection = user_db.users
        user_data = user_collection.find_one({'user_email':user_email})
        if user_data:
            hashed_password = user_data['password']
            if bcrypt.checkpw(entered_password.encode('utf-8'), hashed_password):
                user = User(
                    user_id=user_data['_id'],
                    user_email=user_data['user_email'],
                    game_list=user_data.get('game_list', [])
                )
                login_user(user, remember=True, duration=datetime.timedelta(days=30))
                return redirect(url_for('.load_main_page'))
            else:
                return render_template('index.html', error='Please provide correct email or password.'), 401   
        else:
            return render_template('index.html', error=f'No user exists with {user_email}.'), 401

            
@blog.route('/log_out')
def log_out():
    """Logs out the user."""
    logout_user()
    return redirect(url_for('.load_main_page'))

@blog.route('/delete_account')
def delete_account():
    """Deletes the user account"""
    User.delete(current_user.user_id)
    logout_user()
    return redirect(url_for('.load_main_page'))