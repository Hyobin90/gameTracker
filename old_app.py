""" Entry point of the app """
import asyncio
import argparse
from server.models.mysqldb import create_mysql_db, init_pool, local_db_host, local_db_passwd, local_db_port, local_db_user, game_db_schema_path, query_db_with_pool
import os
from server.controllers.game_manager import GameManager


async def main():
    # Initialize `game_db`
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    await create_mysql_db(host=local_db_host, port=local_db_port, user=local_db_user, passwd=local_db_passwd, db_name='game_db', schema_path=game_db_schema_path)
    db_connection_pool = await init_pool(host=local_db_host, port=local_db_port, user=local_db_user, passwd=local_db_passwd)
    game_manager = GameManager(pool=db_connection_pool, loop=loop)
    game = await game_manager.resolve_game_entry('khazan', db_connection_pool)

    # The last to step before closing the app
    db_connection_pool.close()
    await db_connection_pool.wait_closed()

asyncio.run(main())

# if __name__ == '__main__':
#     arg_parser = argparse.ArgumentParser(description='Register your game of interest')
    
#     arg_parser.add_argument('search_title', type=str, help='The full name of the title to search for.')
#     arg_parser.add_argument('--page_num', type=int, default=10, help='The number of elements to check at once.')
#     arg_parser.add_argument('--offset', type=int, default=0, help='The number of elements to ignore. Use this only when to search repeatedly.')

#     args = arg_parser.parse_args()

#     asyncio.run(resolve_game_entry(args.search_title, args.page_num, args.offset))


