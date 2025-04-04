import bcrypt
from bson.objectid import ObjectId
from flask_login import UserMixin
from server.models.mongodb import connect_mongodb

class User(UserMixin):
    def __init__(self, user_id, user_email, game_list):
        self.user_id = user_id # `_id` genearted by MongoDB automatcially
        self.user_email = user_email
        self.game_list = game_list


    def get_id(self):
        return str(self.user_id)


    @staticmethod
    def find_user(user_id: str = '', user_email: str = '') -> 'User':
        """Retrieves a user with either of the given `user_id` or `user_email`
        
        Args:
            user_id: The user_id to search for a specific user.
            user_email: the user_email to search for a specific user.
        """
        if not user_id and not user_email:
            raise RuntimeError('Provide either of user_id or user_email.')

        user_db = connect_mongodb('users')
        user_collection = user_db.users

        query = {"$or": []}
        filter = [{'user_email': user_email}]

        if user_id:
            obj_id = ObjectId(user_id)
            filter.append({'_id': obj_id})

        query["$or"] = filter
        user_data = user_collection.find_one(query)
        if user_data:
            return User(user_data['_id'], user_data['user_email'], ['game_list'])
        return None


    @staticmethod
    def create_user(user_email: str, user_password: str) -> 'User':
        """Creates a user with the given email after verifying if a user with the same email exists.
        
        Args:
            user_email: the email address to create a User with.
        Returns:
            An instance of the user.
        """
        user = User.find_user(user_email=user_email)
        if not user:
            user_db = connect_mongodb('users')
            user_collection = user_db.users
            hashed_password = User.hash_password(user_password)
            user_collection.insert_one({
                'user_email': user_email,
                'password': hashed_password
            })
            return User.find_user(user_email=user_email)
        else:
            raise RuntimeError(f'A user already exists with the email: {user_email}')
        
    
    @staticmethod
    def delete(user_id) -> None:
        """Deletes users by its `user_id`.
        
        Args:
            user_id: the user ID of the user to be deleted.
        """
        user_db = connect_mongodb('users')
        user_collection = user_db.users

        obj_id = ObjectId(user_id)
        user_collection.delete_one({'_id':obj_id})

    
    @staticmethod
    def hash_password(password) -> bytes:
        """Hashes the password for security and returns it.
        
        Args:
            password: a password to hash.
        Returns:
            the hashed password.
        """
        bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()

        return bcrypt.hashpw(bytes, salt)