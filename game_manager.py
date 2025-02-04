"""Manage games by registering, and updating them."""
from datetime import datetime
from db_manager import query_db_with_pool, IntegrityError, query_wikidata
from game import Game
from SPARQLWrapper import JSON
from tabulate import tabulate # temp mesure for user interaction
from typing import Any, Dict, List, Optional
import re
import pprint


URL_METACRITIC = 'https://www.metacritic.com/game/'
URL_OPENCRITIC = 'https://opencritic.com/game/'
date_pattern = r'^\d{4}-\d{2}-\d{2}$'


async def resolve_game_entry(search_title: str, db_connection_pool, search_page_num: int = 10, search_offset: int = 0) -> Game:
    """Creates an instance of `Game` class when it's found in game_db or Wikidata.
    
    Args:
        search_title: the user's input for the game title to search for.
        db_connection_pool: the pool of Connection to use to connect to DB. This will only used by the methods requiring `game_db`.
        search_page_num: the number of pages to look into at once when searching Wikidata.
        search_offset: the number of pages to ignore to retrieve the next batch of pages when searching Wikidata.
    """
    game_of_interest: Game = None
    game_candidates: List[Dict[str, str]] = []
    selected_candidate: Dict[str, str] = None

    try:
        if not search_title:
            search_title = input('Put the title of the game.\n').lower() # TODO a place holder for the client request.
        # TODO GTPS-62 Try to get game data from game_db
        # response = await _search_game_in_gameDB(search_title) # offset feature, is it necessary?
        # game_candiates = _make_cadidate_list(response) # TODO GTPS-62 making a list of game candidates out of the games found from game DB

        candidate_loop_count = 0
        candidate_loop_limit = 3
        while not game_candidates and (candidate_loop_count < candidate_loop_limit):
            # TODO When the game doesn't exist in game_db 
            # Try to get metadata of the game in `Wikidata
            search_offset += search_page_num * candidate_loop_count
            response = await _search_wikidata(search_title, search_page_num, search_offset)  # Be careful with search_offset.
            #pprint.pprint(response) # For debugging
            game_candidates = _make_cadidate_list(response)
            candidate_loop_count += 1
            #print(f'For debugging, game_candidates : {game_candidates}')  # For debugging

            if not game_candidates:
                #search_title = input(f'Nothing has been found with {search_title}. Please try agin or with another title.\n')
                continue
            break
        
        if game_candidates:
            selected_candidate = await _display_game_candidates(game_candidates, search_title, search_page_num, search_offset, db_connection_pool)
            if candidate_loop_count != 0:
                await _add_new_game_to_db(selected_candidate, db_connection_pool)
                
        # TODO GTPS-76 when the game was not found in gameDB initially, it should be attempted again to send the query to game db here.
        game_of_interest = _fill_game_entry(selected_candidate)
        return game_of_interest

    # Error catching for SPARQL query
    except Exception as e:
        print(f'Error occurred while resolving game entry : {e}')


async def _search_wikidata(search_title, search_page_num, search_offset) -> Any:
    """Searches for a game in Wikidata"""
    query_template = """
    SELECT DISTINCT ?item ?titleLabel (GROUP_CONCAT(DISTINCT ?platformLabel; separator=", ") AS ?platforms)
    WHERE {{
        ?item wdt:P31 ?type.
        VALUES ?type {{wd:Q7889 wd:Q64170203}}.
        
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
    GROUP BY ?item ?titleLabel ?platforms
    LIMIT {search_page_num}
    OFFSET {search_offset}
    """
    values = {'search_title': f'{search_title}',
              'search_page_num': f'{search_page_num}',
              'search_offset': f'{search_offset}'}
    response = await query_wikidata(query_template, values)
    return response


def _make_cadidate_list(sparql_response) -> List[Dict[str, str]]:
    ''' Makes a list of found games as candidates for the user to choose as a target game.

    Args:
        sparql_response : The response of SPARQL query containing probably multiple pages of games.

    Returns:
        candidates : A list of dictionaries containing multiple games' metadata.
    '''
    # TODO GTPS-62 add logic to handle the case where the games are found in game_db.
    wikidata_code = '' # wikidata code
    platforms = ''  # platforms
    title = ''  # titleLabel

    target_keys = ['item', 'titleLabel']

    game_candiates: List[Dict[str, Any]] = []

    for element in sparql_response['results']['bindings']:  # -> List of Dicts, `element` is a dict
        if all(key in element for key in target_keys):  # Lower the level of detail here
            temp_wikidata_code = element.get('item', {}).get('value', None)
            wikidata_code = temp_wikidata_code.rsplit('/', 1)[-1] if temp_wikidata_code is not None else None
            platforms = element.get('platforms', {}).get('value', 'not available')
            title = element.get('titleLabel', {}).get('value', None)
            
            candidate = {
                'wikidata_code': wikidata_code,
                'platforms': platforms,
                'title': title
            }

            if 'PlayStation' in candidate.get('platforms'): # filtering for PlayStation
                game_candiates.append(candidate)

    return game_candiates


async def _display_game_candidates(game_candidates: List[Dict[str, str]], search_title: str, search_page_num: int, search_offset: int, db_connection_pool) -> Dict[str, str]:
    """Displays found candidates to the user to choose.
    
    Args:
      game_candiates: A list of dictionaries containing games found in `WikiData`.
      search_title: A string used to search for the game.
      search_page_num: The number of elements in `Wikidata` to be grabbed while searching.
      search_offset: The number of elements to be ignored. This is only used when the search with the same `search_title` is requested again. 
      db_connection_pool: the pool of Connection to use to connect to DB. This will only used by the methods requiring `game_db`.
    
    Returns:
      A dictionary of selected game.
    """
    # Create a table to display
    temp = []
    for index, candidate in enumerate(game_candidates):
        temp.append({'index': index + 1, 'title': candidate.get('title'), 'platforms': candidate.get('platforms'), 
                     'wikidata': f'https://www.wikidata.org/wiki/{candidate.get('wikidata_code')}'})
    print('Choose the desired game from the list.')
    print(tabulate(temp, headers='keys', tablefmt='rounded_outline'))

    while True:
        while True:
            try:
                choice = int(input('Enter the number of the game that you want.\nIf you want to search for the same title one more time, press 0.\n'))
            except ValueError as e:
                print('Please enter a valid number.\nIf the desired is not present in the list, press 0.\n')
                continue
            break
        if choice == 0:
            new_search_title = input('Put the title of the game.\n')
            if search_title == new_search_title:
              search_offset = search_offset + search_page_num # if the search is requested with the same title, the next page should be provided.
            await resolve_game_entry(new_search_title, db_connection_pool, search_page_num, search_offset) # TODO this part might create an infinite loop.
        elif 1 <= choice <= len(temp):
            print(f'You selected {temp[choice-1]["title"]}')
            return game_candidates[choice-1]


def _fill_game_entry(selected_candidate: Dict[str, str]) -> Game:
    pass
# TODO GTPS-62 game_of_interest should be created from gameDB
    """Creates an instance of `Game` class.
    
    Args:
      selected_candidated: A list of dictionaries of metadata retrieved from `Wikidata`.
      manually_created: If True, the metadata of the game is left empty.

    Returns:
      An instance of Game.
    """
    game_of_interest: Game = None
    title = ''
    manually_created = True

    if selected_candidate:
        title = selected_candidate.get('title')
        manually_created = False
    else:
        print('The game cannot be found in our database or `WikiData` now.\nCreate the entry manually. Missing details can be filled up later.') # TODO be more specific by asking more info?
        title = input('Please enter the game\'s full title.')
        _add_new_game_to_db({'title': title}, manually_created) # TODO GTPS-59, in case this is a whole new game. 

    game_of_interest = Game(title, manually_created, selected_candidate)
    game_of_interest.set_purchase()
    game_of_interest.set_play_platform()
    game_of_interest.set_expectation()
    game_of_interest.fill_meta_score()
    game_of_interest.fill_open_score()

    return game_of_interest


async def _add_new_game_to_db(new_game: Dict[str, str], db_connection_pool, manually_created: bool = False):
    """Adds a new game to the game DB by sending a query to `game_db`.
    
    Args:
        new_game: a dictionary of a new game to be added into game_db.
        db_connection_pool: the pool of Connection to use to connect to DB
        manually_created: If True, this entry should be updated in the future.
    """
    try:
        # info from the inital query from Wikidata.
        wikidata_code = new_game.get('wikidata_code', None)
        title = new_game.get('title', '')

        # retrieve metadata from Wikidata
        metadata = await _get_metadata_from_wikidata(wikidata_code)

        # To `game_table`
        aliases = metadata.get('aliases', None)
        genres = metadata.get('genres', None)
        developers = metadata.get('developers', None)
        publishers = metadata.get('publishers', None)
        
        # TODO separate the query into 2
        query_insert_game = """
        USE game_db;
        INSERT INTO game_table 
        (title, aliases, wikidata_code, genres, developers, publishers, manually_created)
        VALUES(%s, %s, %s, %s, %s, %s, %s);
        """
        value_insert_game = (title, aliases, wikidata_code, genres, developers,
                             publishers, 1 if manually_created else 0)
        # Sends query to `game_table` to add the new game.
        await query_db_with_pool(db_connection_pool, 'INSERT', query_insert_game, value_insert_game)

        # Sends query to retrieve `game_id`
        query_game_id = """
        SELECT LAST_INSERT_ID() AS game_id;
        """
        game_id_response = await query_db_with_pool(db_connection_pool, 'SELECT', query_game_id)
        game_id = game_id_response[0].get('game_id', None)

        # To `date_platform_table`
        dates_and_platforms = metadata.get('dates_and_platforms', {})

        base_query = """
        USE game_db;
        INSERT INTO date_platform_table
        (game_id, release_date, released, platforms, regions)
        """
        complete_query = lambda base_query, length: base_query + "VALUE " + ", ".join(['(%s, %s, %s, %s, %s)'] * length) + ';'
        query_insert_date = complete_query(base_query, len(dates_and_platforms))
        value_insert_date = tuple()
        for element in dates_and_platforms:
            release_date = _process_release_date(element.get('release_date', None))
            released = 0
            if release_date is not None:
                release_date = release_date[:10]
                released = 1 if release_date and datetime.strptime(release_date, '%Y-%m-%d') <= datetime.today() else 0
            platforms = element.get('platforms', None)
            regions = element.get('regions', None)
            value_insert_date += (game_id, release_date, released, platforms, regions) 

        # Sends query to `release table` to add release data platforms and etc.
        await query_db_with_pool(db_connection_pool, 'INSERT', query_insert_date, value_insert_date)
    except IntegrityError as e:
        raise IntegrityError(f'IntegrityError has occurred. {title} is already present in the DB. Please check. | {e.__cause__}') from e
    except Exception as e:
        # TODO Leave this for catching errors that might happen in the future 
        print(f'Error occurred while adding a new game into gameDB | {e}')


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
        ?item skos:altLabel ?alias.
        FILTER(LANG(?alias)="en")

        ?item wdt:P136 ?genre.
        ?genre rdfs:label ?genreLabel.
        FILTER(LANG(?genreLabel)="en")

        ?item wdt:P178 ?developer.
        ?developer rdfs:label ?developerLabel.
        FILTER(LANG(?developerLabel)="en")

        ?item wdt:P123 ?publisher.
        ?publisher rdfs:label ?publisherLabel.
        FILTER(LANG(?publisherLabel)="en")
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