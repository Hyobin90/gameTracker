import asyncio
from server.controllers.game_manager import GameManager
from server.models.mysqldb import init_db, local_db_host, local_db_passwd, local_db_port, local_db_user, game_db_schema_path


# Initializes game_db and creates an instance of GameManager.
# Note that due to the limit of Flask, the async functions are called synchronously.
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

game_db_pool = _loop.run_until_complete(init_db(host=local_db_host, port=local_db_port, user=local_db_user, 
                                passwd=local_db_passwd, db_name='game_db', schema_path=game_db_schema_path))
game_manager = GameManager(game_db_pool)