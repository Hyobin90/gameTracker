import bcrypt
from bson.objectid import ObjectId
from flask_login import UserMixin
from server.models.game import Game
from server.models.mongodb import connect_mongodb
from typing import List


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
            return User(user_data['_id'], user_data['user_email'], user_data['game_list'])
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
                'password': hashed_password,
                'game_list': []
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


    def add_game(self, target_game_data):
        """Adds the target game into the user's game list.
        
        Args:
            target_game_data: the game data to add into the user's game list.
        """
        # Call methods from Game class when needed
        # For now, it's only for `released` but it will expand to update other attributes such as Metacrtic score
        if not target_game_data['released']:
            target_game = Game(**target_game_data)
            target_game_data['released'] = target_game.released

        self.game_list.append(target_game_data)
        user_db = connect_mongodb('users')
        user_collection = user_db.users

        user_collection.update_one(
            {'_id': self.user_id},
            {'$addToSet': {'game_list': target_game_data}}
        )


    def fetch_game_list(self):
        """Fetches the game list of the current user by validating each game up to date."""
        for game in self.game_list:
            self.validate_game(game)

        return self.game_list
    

    def validate_game(self, game: Game) -> None:
        """Validates a game's status.
        
        Args:
            game: The game to validate
        """
        # TODO call game.update_status()
        # Only if game.released is false or None
        if not game['released']:
            game._is_released()
