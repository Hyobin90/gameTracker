"""Manage games by registering, and updating them."""
from datetime import datetime
from db_manager import query_db_with_pool, IntegrityError, query_wikidata
from game import Game
import httpx
from tabulate import tabulate # temp mesure for user interaction
from typing import Any, Dict, List, Optional


URL_METACRITIC = 'https://www.metacritic.com/game/'
URL_OPENCRITIC = 'https://opencritic.com/game/'
date_pattern = r'^\d{4}-\d{2}-\d{2}$'


async def resolve_game_entry(search_title: str, db_connection_pool, search_page_num: int = 10, search_offset: int = 0) -> Optional[Game]:
    """Creates an instance of `Game` class when it's found in game_db or Wikidata.
    
    Args:
        search_title: the user's input for the game title to search for.
        db_connection_pool: the pool of Connection to use to connect to DB. This will only used by the methods requiring `game_db`.
        search_page_num: the number of pages to look into at once when searching Wikidata.
        search_offset: the number of pages to ignore to retrieve the next batch of pages when searching Wikidata.
    """
    try:
        response = await _search_game_db(search_title, db_connection_pool)
        candidates_from_game_db = _make_candiate_list_game_db(response)

        if candidates_from_game_db:
            selected_candidate = _display_game_candidates(candidates_from_game_db, 'game_db')
            if selected_candidate:
                print('The game has been found in game_db')
                # TODO GTPS-49 have it return the data from game_table and date_platform_table no in Game
                # TODO change required for the client
                return Game(selected_candidate)

        print('The game was not found in game_db, trying in Wikidata')
        response = _cirrus_searrch_wikidata(search_title)
        candidates_from_wikidata = _make_cadidate_list_wikidata(response)

        if candidates_from_wikidata:
            selected_candidate = _display_game_candidates(candidates_from_wikidata, 'wikidata')
            if selected_candidate:
                await _add_return_new_game(db_connection_pool, new_game=selected_candidate)
                # TODO GTPS-49 have it return the data from game_table and date_platform_table no in Game
                # TODO GTPS-49 have it return the new game data right away(game_table, date_platform_table)
                # TODO change required for the client
                return Game(selected_candidate)

        print('The game was not even found in Wikidata. Please try again with another name.')
        return None
    
    except IntegrityError as e:
        raise IntegrityError(f'IntegrityError has occurred. | {e.__cause__}') from e
    except Exception as e:
        raise RuntimeError(f'Error occurred in `resolve_game_entry()`: {e}') from e


async def _search_game_db(search_title, db_connection_pool) -> Any:
    """Searches game_db for a game"""
    select_query = 'SELECT * FROM game_table WHERE MATCH(title, aliases) AGAINST(%s IN NATURAL LANGUAGE MODE);'
    select_values = (search_title)
    await query_db_with_pool(db_connection_pool, 'USE', 'USE game_db;')
    response = await query_db_with_pool(db_connection_pool, 'SELECT', select_query, select_values)
    return response


def _search_for_wikidata_code(search_title: str) -> List[str]:
    """Searches Wikidata to get the entity codes of entitis that match the search title."""
    url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': search_title,
        'srnamespace': 0,
        'format': 'json'
    }

    response = httpx.get(url=url, params=params)
    response.raise_for_status()
    data = response.json()
    codes = []
    for element in data['query']['search']:
        codes.append(element['title'])
    return codes


def _saerch_for_games_with_codes(codes: List[str]) -> Any:
    """With the given Wikidata entity codes, retrieve the entities."""
    formatted_codes = '| '.join(codes)
    url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': formatted_codes,
        'srnamespace': 0,
        'format': 'json'
    }

    response = httpx.get(url=url, params=params)
    response.raise_for_status()
    data = response.json()
    return data

async def _search_wikidata(search_title, search_page_num, search_offset) -> Any:
    """Searches Wikidata for a game"""
    query_template = """
    SELECT DISTINCT ?item ?titleLabel ?is_DLC (GROUP_CONCAT(DISTINCT ?platformLabel; separator=", ") AS ?platforms)
    WHERE {{
        ?item wdt:P31 ?type.
        VALUES ?type {{wd:Q7889 wd:Q64170203 wd:Q1066707 wd:Q209163}}.
        BIND(IF(?type = wd:Q1066707 || ?type = wd:Q209163, 1, 0) AS ?is_DLC).
        
        ?item rdfs:label ?titleLabel.
        FILTER(LANG(?titleLabel)="en").
    
        OPTIONAL{{
            ?item skos:altLabel ?search_alias. 
            FILTER(LANG(?search_alias)="en").
        }}
    
        FILTER(CONTAINS(LCASE(?titleLabel), LCASE("{search_title}")) || CONTAINS(LCASE(?search_alias), LCASE("{search_title}"))).
    
        OPTIONAL {{
            ?item p:P400 ?platformNode.
            ?platformNode ps:P400 ?platformCode.
            ?platformCode rdfs:label ?platformLabel.
            FILTER(LANG(?platformLabel) = "en")
        }}
    }}
    GROUP BY ?item ?titleLabel ?is_DLC ?platforms
    LIMIT {search_page_num}
    OFFSET {search_offset}
    """
    values = {'search_title': f'{search_title}',
              'search_page_num': f'{search_page_num}',
              'search_offset': f'{search_offset}'}
    response = await query_wikidata(query_template, values)
    return response


def _make_candiate_list_game_db(sql_response) -> List[Dict[str, str]]:
    """Makes a list of found games as candidates from game_db for the user to choose as a target game.

    Args:
        sql_response : The response of SQL query containing games from game_db.

    Returns:
        game_candidates : A list of dictionaries containing multiple games' metadata.
    """
    # not yet implemented
    # pro_enhanced = None
    # meta_critic_score = 0
    # meta_user_socre = 0
    # open_ciritic_score = 0
    # open_user_score = 0
    # my_score = 0

    game_candiates: List[Dict[str, Any]] = []

    for element in sql_response:
        candidate = {
            'title': element.get('title', None),
            'is_DLC': element.get('is_DLC', None),
            'aliases': element.get('aliases', None),
            'wikidata_code': element.get('wikidata_code', None),
            'genres': element.get('genres', None),
            'developers': element.get('developers', None),
            'publishers': element.get('publishers', None),
            }
        game_candiates.append(candidate)

    return game_candiates


def _make_cadidate_list_wikidata(sparql_response) -> List[Dict[str, str]]:
    """Makes a list of found games as candidates from Wikidata for the user to choose as a target game.

    Args:
        sparql_response : The response of SPARQL query containing probably multiple pages of games.

    Returns:
        game_candiates : A list of dictionaries containing multiple games' metadata.
    """
    target_keys = ['item', 'titleLabel']

    game_candiates: List[Dict[str, Any]] = []

    for element in sparql_response['results']['bindings']:  # -> List of Dicts, `element` is a dict
        if all(key in element for key in target_keys):  # Lower the level of detail here
            wikidata_link = element.get('item', {}).get('value', None)
            platforms = element.get('platforms', {}).get('value', 'not available')
            title = element.get('titleLabel', {}).get('value', None)
            is_dlc = element.get('is_DLC', {}).get('value', None)
            
            candidate = {
                'wikidata_link': wikidata_link,
                'platforms': platforms,
                'title': title,
                'is_DLC': is_dlc
            }

            game_candiates.append(candidate)

    return game_candiates


def _display_game_candidates(game_candidates: List[Dict[str, str]], data_source: str) -> Optional[Dict[str, str]]:
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
    for index, candidate in enumerate(game_candidates):
        if data_source == 'game_db':
            temp.append({'index': index + 1,
                         'title': candidate.get('title'),
                         'is_DLC': 'Yes' if candidate.get('is_DLC') == 1 else 'No',
                         'genres': candidate.get('genres', 'N/A'),
                         'developers': candidate.get('developers', 'N/A'),
                         'publishers': candidate.get('publishers', 'N/A'),
                         'wikidata': f"https://www.wikidata.org/wiki/{candidate.get('wikidata_code')}" if candidate.get('wikidata_code', None) != None else 'N/A'})
        elif data_source == 'wikidata':
            temp.append({'index': index + 1,
                         'title': candidate.get('title'),
                         'is_DLC': candidate.get('is_DLC'),
                         'platforms': candidate.get('platforms'), 
                         'wikidata': candidate.get('wikidata_link')})
    print('Choose the desired game or parent game from the list.')
    print(tabulate(temp, headers='keys', tablefmt='rounded_outline'))

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
            return game_candidates[choice-1]


async def _add_return_new_game(db_connection_pool, new_game: Dict[str, str]) -> Game:
    """Adds a new game into `game_db` and return it as Game.
    
    Args:
        db_connection_pool: the pool of Connection to use to connect to DB.
        new_game: a dictionary of a new game to be added into game_db.

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
        title = new_game.get('title')
        is_DLC = True if new_game.get('is_DLC') == '1' else False
        wikidata_code = new_game.get('wikidata_link').rsplit('/', 1)[-1]

        metadata = await _get_metadata_from_wikidata(wikidata_code)
        # TODO Implement features for the critics
        # metascores = get_metacritic()
        # openscores = get_opencritic()
        aliases = metadata.get('aliases', None)
        genres = metadata.get('genres', None)
        developers = metadata.get('developers', None)
        publishers = metadata.get('publishers', None)
        dates_and_platforms = metadata.get('dates_and_platforms', {})

        if is_DLC:
            response = await _search_game_db(title, db_connection_pool)
            parent_cadiates_from_game_db = _make_candiate_list_game_db(response)
            selected_parent = _display_game_candidates(parent_cadiates_from_game_db, 'game_db')
            if not selected_parent:
                raise RuntimeError(f'The original game of {title} is not present in `game_db`')
            parent_id = selected_parent.get('game_id')
            aliases += selected_parent.get('aliases', '')
            genres += selected_parent.get('genres', '')
            developers += selected_parent.get('developers', '')
            publishers += selected_parent.get('publishers', '')

        # Sends query to `game_table` to add the new game.
        query_insert_game = """
        USE game_db;
        INSERT INTO game_table 
        (title, is_DLC, aliases, wikidata_code, genres, developers, publishers, parent_id)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s);
        """
        value_insert_game = (title, is_DLC, aliases, wikidata_code, genres, developers, publishers, parent_id)
        await query_db_with_pool(db_connection_pool, 'INSERT', query_insert_game, value_insert_game)

        # Sends query to retrieve `game_id`
        game_id_response = await query_db_with_pool(db_connection_pool, 'SELECT', 'SELECT LAST_INSERT_ID() AS game_id;')
        game_id = game_id_response[0].get('game_id', None)

        # Sends query to `release table` to add release data platforms and etc.
        base_query = """
        USE game_db;
        INSERT INTO date_platform_table
        (game_id, release_date, released, platforms, regions)
        """
        complete_query = lambda base_query, length: base_query + "VALUE " + ", ".join(['(%s, %s, %s, %s, %s)'] * length) + ';'
        query_insert_data = complete_query(base_query, len(dates_and_platforms))
        value_insert_data = tuple()
        for element in dates_and_platforms:
            release_date = _process_release_date(element.get('release_date', None))
            released = 0
            if release_date is not None:
                release_date = release_date[:10]
                released = 1 if release_date and datetime.strptime(release_date, '%Y-%m-%d') <= datetime.today() else 0
            platforms = element.get('platforms', None)
            regions = element.get('regions', None)
            value_insert_data += (game_id, release_date, released, platforms, regions)
        await query_db_with_pool(db_connection_pool, 'INSERT', query_insert_data, value_insert_data)

    except IntegrityError as e:
        raise IntegrityError(f'IntegrityError has occurred. {title} is already present in the DB. Please check. | {e.__cause__}') from e
    except Exception as e:
        raise RuntimeError(f'Error occurred in `_add_return_new_game()` | {e}') from e


async def _get_metadata_from_wikidata(wikidata_code: str) -> Dict[str, str]:
    """ Retrieves the following metadata of the target game from `Wikidata`:
        aliases, genres, developers, publishers, platforms and publication data.

        Args:
            wikidata_code: the entity code of the target game in `Wikidata`.
 
    """
    template_simple_metadata = """
    SELECT DISTINCT
        (GROUP_CONCAT(DISTINCT ?alias; separator=", ") AS ?aliases)
        (GROUP_CONCAT(DISTINCT ?genreLabel; separator=", ") AS ?genres)
        (GROUP_CONCAT(DISTINCT ?developerLabel; separator=", ") AS ?developers)
        (GROUP_CONCAT(DISTINCT ?publisherLabel; separator=", ") AS ?publishers)

    WHERE {{
        BIND(wd:{wikidata_code} AS ?item)
        OPTIONAL {{
            ?item skos:altLabel ?alias.
            FILTER(LANG(?alias)="en")
        }}

        OPTIONAL {{
            ?item wdt:P136 ?genre.
            ?genre rdfs:label ?genreLabel.
            FILTER(LANG(?genreLabel)="en")
        }}

        OPTIONAL {{
            ?item wdt:P178 ?developer.
            ?developer rdfs:label ?developerLabel.
            FILTER(LANG(?developerLabel)="en")
        }}

        OPTIONAL {{
            ?item wdt:P123 ?publisher.
            ?publisher rdfs:label ?publisherLabel.
            FILTER(LANG(?publisherLabel)="en")
        }}
    }}
    """

    template_date_platform = """
        SELECT DISTINCT
        ?publicationDateLabel 
        (GROUP_CONCAT(DISTINCT ?finalPlatformLabel; separator=", ") AS ?platforms)
        ?region
        WHERE {{
            BIND(wd:{wikidata_code} AS ?item)
            OPTIONAL {{
                ?item p:P577 ?publicationDateNode.
                FILTER NOT EXISTS {{
                    ?publicationDateNode pq:P2241 ?deprecationReason
                }}
                ?publicationDateNode ps:P577 ?publicationDateLabel.
                OPTIONAL {{
                    ?publicationDateNode pq:P400 ?platformNodeFromDate.
                    ?platformNodeFromDate rdfs:label ?platformLabelFromDate.
                    FILTER(LANG(?platformLabelFromDate) = "en").
                }}
                OPTIONAL {{
                    ?publicationDateNode pq:P291 ?placeOfDistribution.
                    ?placeOfDistribution rdfs:label ?region.
                    FILTER(LANG(?region) = "en")
                }}
            }}

            OPTIONAL {{
                ?item p:P400 ?platformNode.
                ?platformNode ps:P400 ?platformCode.
                ?platformCode rdfs:label ?platformLabel.
                FILTER(LANG(?platformLabel) = "en").
            }}

            BIND(COALESCE(?platformLabelFromDate, ?platformLabel) AS ?finalPlatformLabel).
        }}

        GROUP BY ?publicationDateLabel ?platforms ?region
    """
    
    # it's expected to have one entry
    simple_metadata = await query_wikidata(template_simple_metadata, {'wikidata_code':wikidata_code})
    # there might be multiple entries
    date_platform_metadata = await query_wikidata(template_date_platform, {'wikidata_code':wikidata_code})

    aliases = simple_metadata['results']['bindings'][0].get('aliases', {}).get('value', None)
    genres = simple_metadata['results']['bindings'][0].get('genres', {}).get('value', None)
    developers = simple_metadata['results']['bindings'][0].get('developers', {}).get('value', None)
    publishers = simple_metadata['results']['bindings'][0].get('publishers', {}).get('value', None)

    dates_and_platforms: List[Dict[str, str]] = []
    for element in date_platform_metadata['results']['bindings']:
        release_date = element.get('publicationDateLabel', {}).get('value', None)
        platforms = element.get('platforms', {}).get('value', None)
        regions = element.get('region', {}).get('value', None)

        temp_entry = {
            'release_date': release_date,
            'platforms': platforms,
            'regions': regions
            }

        dates_and_platforms.append(temp_entry)
    
    metadata = {
        'aliases': aliases,
        'genres': genres,
        'developers': developers,
        'publishers': publishers,
        'dates_and_platforms': dates_and_platforms
    }

    return metadata


def _process_release_date(release_date: Optional[str]) -> str:
    """Hanldes release dates when it's yyyy-01-01 by modifying it to yyyy-12-31 to indicate the title comes out somewhere in the year.
    
    Args:
        release_date: the release date to process.
    Returns:
        a processed release date.
    """
    if release_date is None:
        return None
    
    release_date = release_date[:10]
    date_elements = release_date.split('-', 2)
    year = date_elements[0]
    month = date_elements[1]
    day = date_elements[2]

    if month == '01' and day == '01':
        return f'{year}-12-31'
    else:
        return release_date
