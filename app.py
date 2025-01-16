""" Entry point of the app """
import asyncio
import argparse
from game_manager import search_target_game


asyncio.run(search_target_game('witcher 4'))

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Register your game of interest')
    
    arg_parser.add_argument('search_title', type=str, help='The full name of the title to search for.')
    arg_parser.add_argument('--page_num', type=int, default=10, help='The number of elements to check at once.')
    arg_parser.add_argument('--offset', type=int, default=0, help='The number of elements to ignore. Use this only when to search repeatedly.')

    args = arg_parser.parse_args()

    asyncio.run(search_target_game(args.search_title, args.page_num, args.offset))