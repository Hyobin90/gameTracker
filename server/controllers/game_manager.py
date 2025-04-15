"""Manage games by registering, and updating them."""
from datetime import datetime
from server.models.mysqldb import query_db_with_pool, IntegrityError
from server.models.game import Game
import httpx
from tabulate import tabulate # temp mesure for user interaction
from typing import Any, Dict, List, Optional, Union
import os
import json

URL_METACRITIC = 'https://www.metacritic.com/game/'
URL_OPENCRITIC = 'https://opencritic.com/game/'
date_pattern = r'^\d{4}-\d{2}-\d{2}$'
property_json_path = os.path.join(os.getcwd(), 'server', 'schemas', 'wikidata_properties.json')


class GameManager:
    """A manager class that process data from game_db or Wikidata to create Game instances"""
    def __init__(self, loop, pool):
        self.loop = loop
        self.pool = pool
        self.properties = self._load_json_for_properties(property_json_path)


    async def find_candiates(self, search_title: str):
        """Provides a list of candiates by searching game_db or Wikidata.
        
        Args:
            search_title: the user's input for the game title to search for.
        """
        try:
            candidates = None

            response = await self._search_game_db(search_title)
            if len(response) == 0:
                entity_codes = self._search_wikidata(search_title)
                await self._add_new_games(entity_codes)
                response = await self._search_game_db(search_title)

            candidates = self._make_candidate_list(response)

            return candidates

        except IntegrityError as e:
            raise IntegrityError(f'IntegrityError has occurred. | {e.__cause__}') from e
        except Exception as e:
            raise RuntimeError(f'Error occurred in `find_candiates()`: {e}') from e


    async def _search_game_db(self, search_title) -> Any:
        """Searches game_db for a game"""
        select_query = """
                        SELECT *, MATCH(title, aliases) AGAINST(%s) AS relevance
                        FROM game_table 
                        INNER JOIN date_platform_table
                        ON game_table.game_id = date_platform_table.game_id
                        WHERE MATCH(title, aliases) AGAINST(%s IN NATURAL LANGUAGE MODE)
                        HAVING relevance > 7.0;"""
        select_values = (search_title, search_title)
        await query_db_with_pool(self.pool, 'USE', 'USE game_db;')
        response = await query_db_with_pool(self.pool, 'SELECT', select_query, select_values)
        return response


    def _make_candidate_list(self, response) -> List[Dict[str, str]]:
        """Makes a list of games found in game_db with their metadata.

        Args:
            sql_response : The response of SQL query containing games from game_db.

        Returns:
            game_candidates : A list of dictionaries containing multiple games' metadata.
        """
        game_candidates: List[Dict[str, Any]] = []

        for element in response:
            candidate = {
                'game_id': element.get('game_id', None),
                'release_id': element.get('release_id', None),
                'title': element.get('title', None),
                'is_DLC': element.get('is_DLC', None),
                'aliases': element.get('aliases', None),
                'wikidata_code': element.get('wikidata_code', None),
                'genres': element.get('genres', None),
                'developers': element.get('developers', None),
                'publishers': element.get('publishers', None),
                'release_date': element.get('release_date', None).strftime('%Y-%m-%d'),
                'platforms': element.get('platforms', None)
                }
            game_candidates.append(candidate)

        return game_candidates


    def _search_wikidata(self, search_title: str) -> List[str]:
        """Searches Wikidata to get the entity codes of entities that match the search title."""
        url = 'https://www.wikidata.org/w/api.php'
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': search_title,
            'srnamespace': 0,
            'srlimit': 50,
            'format': 'json',
            'props': 'claims'
        }

        response = httpx.get(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        codes = []
        for element in data['query']['search']:
            codes.append(element['title'])
        return codes


    async def search_game_db_with_id(self, game_id: str, release_id: str) -> Game:
        """Searches game_db with a game_id.
        
        Args:
            game_id: the ID to search game_table for the game with.
            release_id: the ID to search date_platform_table for the game with.
        
        Returns:
            An instance of Game class of the target game.
        """
        target_game = None

        select_query = """
                        SELECT * FROM game_table INNER JOIN date_platform_table
                        ON game_table.game_id = date_platform_table.game_id
                        WHERE game_table.game_id = %s AND date_platform_table.release_id = %s
                        """
        select_values = (game_id, release_id)
        await query_db_with_pool(self.pool, 'USE', 'USE game_db;')
        response = await query_db_with_pool(self.pool, 'SELECT', select_query, select_values)

        target_game = Game(**response[0])
        return target_game


    async def _add_new_games(self, entity_codes: List[str]) -> None:
        """Adds a new game into `game_db` and return it as Game.
        
        Args:
            new_game: a dictionary of a new game to be added into game_db.
            for_prep: a flag to indicate whther it's for filling up game_db.

        Returns:
            An instance of Game of the new game.
        """
        title = None
        is_DLC = None
        wikidata_code = None
        aliases = None
        genres = None
        developers = None
        publishers = None
        dates_and_platforms = None
        parent_id = 'N/A'

        try:
            for entity_code in entity_codes:
                raw_metadata = self._get_metadata(code=entity_code, language='en')
                if raw_metadata is None:
                    continue
                processed_metadata = self._process_game_data_with_code(raw_metadata)

                title = processed_metadata.get('title', None)
                is_DLC = processed_metadata.get('is_DLC', None)
                wikidata_code = entity_code
                aliases = processed_metadata.get('aliases', None)
                genres = processed_metadata.get('genres', None)
                developers = processed_metadata.get('developers', None)
                publishers = processed_metadata.get('publishers', None)
                dates_and_platforms = processed_metadata.get('publication_dates', None)

                # if is_DLC:
                #     response = await self._search_game_db(title)
                #     parent_cadidates_from_game_db = self._make_candiate_list_game_db(response)
                #     selected_parent = self._display_game_candidates(parent_cadidates_from_game_db, 'game_db', is_DLC)
                #     if not selected_parent:
                #         raise RuntimeError(f'The original game of {title} is not present in `game_db`')
                #     parent_id = selected_parent.get('game_id')
                #     aliases += selected_parent.get('aliases', '')
                #     genres += selected_parent.get('genres', '')
                #     developers += selected_parent.get('developers', '')
                #     publishers += selected_parent.get('publishers', '')

                # Sends query to `game_table` to add the new game.
                query_insert_game = """
                USE game_db;
                INSERT INTO game_table 
                (title, is_DLC, aliases, wikidata_code, genres, developers, publishers, parent_id)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s);
                """
                value_insert_game = (title, is_DLC, aliases, wikidata_code, genres, developers, publishers, parent_id)
                await query_db_with_pool(self.pool, 'INSERT', query_insert_game, value_insert_game)

                # Sends query to retrieve `game_id`
                game_id_response = await query_db_with_pool(self.pool, 'SELECT', 'SELECT LAST_INSERT_ID() AS game_id;')
                game_id = game_id_response[0].get('game_id', None)

                # Sends query to `release table` to add release data platforms and etc.
                base_query = """
                USE game_db;
                INSERT INTO date_platform_table
                (game_id, release_date, released, platforms)
                """
                complete_query = lambda base_query, length: base_query + "VALUE " + ", ".join(['(%s, %s, %s, %s)'] * length) + ';'
                if dates_and_platforms:
                    query_insert_data = complete_query(base_query, len(dates_and_platforms))
                    value_insert_data = tuple()
                    for element in dates_and_platforms:
                        release_date = None
                        released = 0
                        try:
                            release_date = datetime.strptime(element.get('publication_date', None), '%Y-%m-%d')
                        except ValueError:
                            release_date = None
                        if release_date is not None:
                                released = 1 if release_date <= datetime.today() else 0
                        platforms = element.get('platforms', None)
                        rel_date_str = datetime.strftime(release_date, "%Y-%m-%d") if release_date is not None else None
                        value_insert_data += (game_id, rel_date_str, released, platforms)
                    await query_db_with_pool(self.pool, 'INSERT', query_insert_data, value_insert_data)
                # elif not for_prep and not dates_and_platforms and is_DLC:
                #     query_insert_data = complete_query(base_query, 1)
                #     parent_platforms = await query_db_with_pool(self.pool, 'SELECT', f'SELECT platforms FROM date_platform_table WHERE game_id = {parent_id} GROUP BY platforms')
                #     platforms = ''
                #     for element in parent_platforms:
                #         platforms = platforms+ ', ' + element['platforms'] if platforms else element['platforms']
                #     value_insert_data = (game_id, '2100-12-31', 0, platforms)
                #     await query_db_with_pool(self.pool, 'INSERT', query_insert_data, value_insert_data)

                print(f'{title} has been added into `game_db`.\n ---------------------------------------------')

        except IntegrityError as e:
            print(f'IntegrityError has occurred : {title} is already present in game_db')
        except Exception as e:
            raise RuntimeError(f'Error occurred in `add_new_game()` | {e}') from e


    def _get_metadata(self, code: str, language: str = 'en', filtering_platforms: List[str] = []) -> Dict:
        """Retrieves metadata from Wikidata With the given entity code."""
        url = 'https://www.wikidata.org/w/api.php'
        params = {
            'action': 'wbgetentities',
            'ids': code,
            'languages': language,
            'format': 'json',
            'props': 'labels|aliases|claims'
        }

        response = httpx.get(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        processed_data = {}
        for entity in data['entities'].values():
            if (not entity.get('claims', {}) or
                not entity.get('claims').get('P31', []) or
                not any(instance.get('mainsnak', {}).get('datavalue').get('value', {})['id'] in ('Q7889', 'Q1066707', 'Q209163')for instance in entity.get('claims', {}).get('P31'))):
                return
            processed_data['platforms'] = [platform.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id', 'N/A') for platform in entity.get('claims', {}).get('P400', {})]

            # filtering for specific platform
            if filtering_platforms and not any(platform in filtering_platforms for platform in processed_data['platforms']):
                return
            processed_data['title'] = entity.get('labels', {}).get(language, {}).get('value', 'N/A')
            processed_data['aliases'] = [alias.get('value', 'N/A') for alias in entity.get('aliases', {}).get(language, {})]
            processed_data['wikidata_code'] = entity.get('id', 'N/A')
            processed_data['is_DLC'] = True if entity.get('claims', {}).get('P31', [])[0].get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id', 'N/A') in ('Q1066707', 'Q209163') else False
            processed_data['genres'] = [genre.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id', 'N/A') for genre in entity.get('claims', {}).get('P136', {})]
            processed_data['developers'] = [developer.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id', 'N/A') for developer in entity.get('claims', {}).get('P178', {})]
            processed_data['publishers'] = [publisher.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id', 'N/A') for publisher in entity.get('claims', {}).get('P123', {})]
            processed_data['publication_dates'] = []
            for date_node in entity.get('claims', {}).get('P577', {}):
                skip_outer = False
                temp = {}
                temp['publication_date'] = date_node.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('time', 'N/A')
                temp['platforms'] = ''
                for qualifier_code, qualifier_node in date_node.get('qualifiers', {}).items():
                    # in case of delayed
                    if qualifier_code == 'P2241':
                        skip_outer = True
                        break
                    if qualifier_code == 'P400':
                        temp['platforms'] = [platform_node.get('datavalue', {}).get('value', {}).get('id', 'N/A') for platform_node in qualifier_node]
                    if not temp['platforms']:
                        temp['platforms'] = processed_data['platforms']
                if skip_outer:
                    continue
                # in case no platforms mentioned
                if not temp['platforms']:
                    temp.update({'platforms': processed_data['platforms']})
                processed_data['publication_dates'].append(temp)
        return processed_data


    def _process_game_data_with_code(self, data_with_code: Dict) -> Dict:
        """Replaces `Wikidata` code in the data with their equivalent values."""
        game_data = {}
        game_data['publication_dates'] = []
        for key, value in data_with_code.items():
            if key in ('genres', 'developers', 'publishers', 'platforms'):
                game_data[key] = self._replace_code(key, value)
            elif key == 'publication_dates':
                for date_platform in value:
                    temp = {}
                    temp['publication_date'] = self._process_release_date(date_platform['publication_date'])
                    temp['platforms'] = self._replace_code('platforms', date_platform['platforms'])
                    game_data[key].append(temp)
            elif key in ('title', 'wikidata_code', 'is_DLC'):
                game_data[key] = value
            elif key in ('aliases'):
                game_data[key] = ', '.join(value)
        return game_data


    def _replace_code(self, property_name: str, codes: str) -> str:
        """Finds and replcaes codes with actual values."""
        values = []
        for code in codes:
            value = self.properties[property_name].get(code, 'N/A')
            values.append(value)

        return ', '.join(values)


    def _process_release_date(self, release_date: Optional[str]) -> str:
        """Hanldes release dates when it's yyyy-01-01 by modifying it to yyyy-12-31 to indicate the title comes out somewhere in the year.
        
        Args:
            release_date: the release date to process.
        Returns:
            a processed release date.
        """
        if release_date is None:
            return None
        
        release_date = release_date[1:11]
        date_elements = release_date.split('-', 2)
        year = date_elements[0]
        month = date_elements[1] if len(date_elements) > 1 else 0
        day = date_elements[2] if len(date_elements) > 1 else 0

        # Only the year is provided
        if month == '00' and day == '00':
            return f'{year}-12-31'
        elif day == '00':
            return f'{year}-{month}-01'
        else:
            return release_date


    def _load_json_for_properties(self, json_path: str):
        """Loads the property data from `wikidata_properties.json` file."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        properties = {}

        for property_name in data:
            temp = {}
            for element in data[property_name]:
                temp[element['code']] = element['label']
            properties[property_name] = temp

        return properties
    

    def _make_candidate_list_wikidata_old(self, wikidata_codes: List[str], language: str = 'en') -> List[Dict[str, str]]:
        url = 'https://www.wikidata.org/w/api.php'
        codes = '|'.join(wikidata_codes)
        params = {
            'action': 'wbgetentities',
            'ids': codes,
            'languages': language,
            'format': 'json',
            'props': 'labels|claims'
        }
        response = httpx.get(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        # title, wikidata link, platform need to be displayed
        game_candidates: List[Dict[str, Any]] = []
        for code, entity in data.get('entities', {}).items():
            temp = {}
            entity_types = [entity_type.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id', 'N/A') for entity_type in entity.get('claims', {}).get('P31', {})]
            target_types = ['Q7889', 'Q1066707', 'Q209163'] # filtering for `video game`, `DLC`, `Expansion Pack`

            if any(target_type in entity_types for target_type in target_types):
                wikidata_link = f'https://www.wikidata.org/wiki/{code}'
                title = entity.get('labels', {}).get(language, {}).get('value', 'N/A')
                platforms = [platform.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id', 'N/A') for platform in entity.get('claims', {}).get('P400', {})]
                temp['wikidata_link'] = wikidata_link
                temp['title'] = title
                temp['platforms'] = self._replace_code('platforms', platforms)
                temp['is_DLC'] = True if any(target_type in entity_types for target_type in ['Q1066707', 'Q209163']) else False

                game_candidates.append(temp)

        return game_candidates


    def _display_game_candidates(self, search_keyword: str, game_candidates: List[Dict[str, str]], data_source: str, is_DLC: bool = False, for_prep: bool = False) -> Optional[Union[Dict[str, str], List[Dict[str, str]]]]:
        # GTPS-49 for the client
        """Displays found candidates to the user to choose.
        
        Args:
            game_candiates: A list of dictionaries containing games found in the data_source
            data_source: The indicator to tell where the data come from either `game_db` or `WikiData`.
        Returns:
            A dictionary of selected game if the user choose the target game from the candiates.
        """
        # Create a table to display
        temp = []
        title = ''
        for index, candidate in enumerate(game_candidates):
            title = candidate.get('title')
            if data_source == 'game_db':
                temp.append({'index': index + 1,
                            'game_id': candidate.get('game_id'),
                            'title': title,
                            'is_DLC': 'Yes' if candidate.get('is_DLC') == 1 else 'No',
                            'genres': candidate.get('genres', 'N/A'),
                            'developers': candidate.get('developers', 'N/A'),
                            'publishers': candidate.get('publishers', 'N/A'),
                            'wikidata': f"https://www.wikidata.org/wiki/{candidate.get('wikidata_code')}" if candidate.get('wikidata_code', None) != None else 'N/A'})
            elif data_source == 'wikidata':
                temp.append({'index': index + 1,
                            'title': title,
                            'platforms': candidate.get('platforms'), 
                            'is_DLC': 'Yes' if candidate.get('is_DLC') else 'No',
                            'wikidata': candidate.get('wikidata_link')})
        if is_DLC:
            print(f'Choose the parent game of {search_keyword}')
        else:
            print(f'Choose the desired game - search keyword : {search_keyword}')
        print(tabulate(temp, headers='keys', tablefmt='rounded_outline'))

        # only for adding data for preparation
        if data_source == 'wikidata' and for_prep:
            if len(temp) > 0:
                return game_candidates

        while True:
            while True:
                try:
                    choice = int(input('Enter the number of the game that you want.\nIf the desired game is not in the list, press 0.\n'))
                except ValueError:
                    print('Please enter a valid number.\nIf the desired is not present in the list, press 0.\n')
                    continue
                break
            if choice == 0:
                return None
            elif 1 <= choice <= len(temp):
                print(f'You selected {temp[choice-1]["title"]}')
                return [game_candidates[choice-1]]
            

    async def resolve_game_entry(self, search_title: str, for_prep: bool = False, search_page_num: int = 10, search_offset: int = 0) -> Optional[Game]:
        """Creates an instance of `Game` class when it's found in game_db or Wikidata.
        
        Args:
            search_title: the user's input for the game title to search for.
            for_prep: a flag to indicate that this method is called for filling the game_db.
            search_page_num: the number of pages to look into at once when searching Wikidata.
            search_offset: the number of pages to ignore to retrieve the next batch of pages when searching Wikidata.
        
        Returns:
            an instance of Game containing the data of the target game if found.
        """
        try:
            candidates_from_game_db = None
            # Check in game_db
            if not for_prep:
                response = await self._search_game_db(search_title)
                candidates_from_game_db = self._make_candiate_list_game_db(response)

            selected_candidate = None
            if candidates_from_game_db:
                selected_candidate = self._display_game_candidates(search_keyword=search_title, game_candidates=candidates_from_game_db, data_source='game_db', for_prep=for_prep)
                if selected_candidate:
                    print('The game has been found in game_db\n-------------------------------')
                    return Game(selected_candidate)

            # Fall back to Wikidata
            print(f'The game, {search_title} was not found in game_db, trying in Wikidata')
            wikidata_codes = self._search_wikidata(search_title)
            candidates_from_wikidata = self._make_candidate_list_wikidata_old(wikidata_codes)

            if candidates_from_wikidata:
                selected_candidate = self._display_game_candidates(search_keyword=search_title, game_candidates=candidates_from_wikidata, data_source='wikidata', for_prep=for_prep)
                if selected_candidate:
                    await self.add_new_game(new_games=selected_candidate, for_prep=for_prep)
                    return Game(selected_candidate)

            print(f'The game, {search_title} was not even found in Wikidata. Please try again with another name.')
            return None
        
        except IntegrityError as e:
            raise IntegrityError(f'IntegrityError has occurred. | {e.__cause__}') from e
        except Exception as e:
            raise RuntimeError(f'Error occurred in `resolve_game_entry()`: {e}') from e