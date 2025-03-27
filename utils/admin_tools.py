import asyncio
from server.models.db_manager import create_db, init_pool, local_db_host, local_db_passwd, local_db_port, local_db_user, game_db_schema_path, query_db_with_pool
from server.controller.game_manager import GameManager
import os
import json
from pprint import pprint
import re


async def main():
    """Fills up the game db from Wikidata using a given json file"""
    # Initialize `game_db`
    await create_db(host=local_db_host, port=local_db_port, user=local_db_user, passwd=local_db_passwd, db_name='game_db', schema_path=game_db_schema_path)
    db_connection_pool = await init_pool(host=local_db_host, port=local_db_port, user=local_db_user, passwd=local_db_passwd, db_name='game_db')

    game_list_json_path = os.path.join(os.getcwd(), 'DB', 'All_PlayStation_Games.json')
    game_titles = []
    filter_conditions = ['Pysical extras', 'Special edition', 'Currency', 'Compilation', 'Digital extras', 'Customization / outfit / skin', 'Upgrade (Skill / Boost)', 'Player unit', 'Other']

    with open(game_list_json_path, 'r', encoding='utf-8') as f:
        game_list_json = json.load(f)
        for game_entry in game_list_json:
            genres = game_entry.get('genres', [])
            if any(genre in filter_conditions for genre in genres):
                continue
            game_title = game_entry['title']
            game_titles.append(game_title)

    game_manager = GameManager()

    for title in game_titles:
        await game_manager.resolve_game_entry(search_title=title, db_connection_pool=db_connection_pool, for_prep=True)
    # The last to step before closing the app
    db_connection_pool.close()
    await db_connection_pool.wait_closed()

asyncio.run(main())

