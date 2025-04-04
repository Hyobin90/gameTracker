import pymongo
from typing import Literal

MONGO_HOST = 'localhost'
MONGO_CONNECTION = pymongo.MongoClient(f'mongodb://{MONGO_HOST}')

# TODO improve the code in case MongoDB completely shuts down
def connect_mongodb(db_name: Literal['users', 'sessions']):
    """Connects to MongoDB.
    
    Args:
        db_name: The name of the database to retrieve.
    
    Returns:
        An instance of the selected database.
    """
    global MONGO_CONNECTION
    try:
        MONGO_CONNECTION.admin.command('hello') # send `hello` command to `admin` db to check the availability of the server
    except:
        MONGO_CONNECTION = pymongo.MongoClient(f'mongodb://{MONGO_HOST}')

    if db_name == 'users':
        return MONGO_CONNECTION.users
    elif db_name == 'sessions':
        return MONGO_CONNECTION.sessions