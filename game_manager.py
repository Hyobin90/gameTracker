"""Manage games by registering, and updating them."""
import asyncio
from async_sparql_wrapper import AsyncSparqlWrapper
from game import Game
import re
from SPARQLWrapper import JSON
from tabulate import tabulate # temp mesure for user interaction
from typing import Any, Dict, List


URL_METACRITIC = 'https://www.metacritic.com/game/'
URL_OPENCRITIC = 'https://opencritic.com/game/'
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
date_pattern = r'^\d{4}-\d{2}-\d{2}$'

async def create_target_game_entry(search_title: str, search_page_num: int = 10, search_offset: int = 0) -> Game:
    game_of_interest: Game = None
    game_candidates: List[Dict[str, str]] = []
    selected_candidate: Dict[str, str] = None

    try:
        candidate_loop_count = 0
        candidate_loop_limit = 3

        while candidate_loop_count < candidate_loop_limit:
            if not search_title:
                search_title = input('Put the title of the game.\n').lower()

            # Try to get metadata of the game in `Wikidata
            response = await _search_games_in_wikidata(search_title, search_page_num, search_offset)  # Be careful with search_offset.
            game_candidates = _make_cadidate_list(response)
            print(f'For debugging, game_candidates : {game_candidates}')  # For debugging

            if not game_candidates:
                search_title = input(f'Nothing has been found with {search_title}. Please try agin or with another title.\n')
                candidate_loop_count += 1
                continue
            break
        
        if game_candidates:
            selected_candidate = await _display_game_candidates(game_candidates, search_title, search_page_num, search_offset)

        game_of_interest = _create_game_entry(selected_candidate)
        return game_of_interest

    # Error catching for SPARQL query
    except Exception as e:
        print(f'Error occurred : {e}')


async def _search_games_in_wikidata(search_title: str, search_page_num: int = 10, search_offset: int = 0) -> Any:
    '''Sends SPARQL query to `Metadata` for a game and returns the response.
    
    Args:
        search_title (str): A game's title to search for in `WikiData`.
        search_offset (int): The number of results to skip from the beginning of the query result set,
                             in case the desired game is not found and this method is called again.

    Returns:
        response : The response of SPARQL query containing probably multiple pages of games.

    '''
    query_game = f"""
    SELECT DISTINCT ?item ?itemLabel ?article ?titleLabel ?publicationDateLabel
          (GROUP_CONCAT(DISTINCT ?platformLabel; separator=", ") AS ?platforms)
          (GROUP_CONCAT(DISTINCT ?genreLabel; separator=", ") AS ?genres)
          (GROUP_CONCAT(DISTINCT ?developerLabel; separator=", ") AS ?developers)
          (GROUP_CONCAT(DISTINCT ?publisherLabel; separator=", ") AS ?publishers)
    WHERE {{
        ?item wdt:P31 ?type.
        VALUES ?type {{ wd:Q7889 wd:Q64170203 }}.
        ?item rdfs:label ?label.
        FILTER(CONTAINS(LCASE(?label), "{search_title}")).
        OPTIONAL {{
            ?article schema:about ?item;
                     schema:inLanguage "en";
                     schema:isPartOf <https://en.wikipedia.org/>.
        }}
        OPTIONAL {{
            ?item wdt:P1476 ?titleLabel.
        }}
        OPTIONAL {{
            ?item p:P577 ?publicationDateNode.
            FILTER NOT EXISTS {{
                ?publicationDateNode pq:P2241 ?deprecationReason
            }}
            ?publicationDateNode ps:P577 ?publicationDateLabel.
            OPTIONAL {{
                ?publicationDateNode pq:P400 ?platformNode.
                ?platformNode rdfs:label ?platformLabel.
                FILTER(LANG(?platformLabel) = "en").
                FILTER(CONTAINS(LCASE(?platformLabel), "playstation 4") || CONTAINS(LCASE(?platformLabel), "playstation 5")).
            }}
        }}
        OPTIONAL {{
            ?item wdt:P136 ?genre.
            ?genre rdfs:label ?genreLabel.
            FILTER(LANG(?genreLabel) = "en").
        }}
        OPTIONAL {{
            ?item wdt:P178 ?developer.
            ?developer rdfs:label ?developerLabel.
            FILTER(LANG(?developerLabel) = "en").
        }}
        OPTIONAL {{
            ?item wdt:P123 ?publisher.
            ?publisher rdfs:label ?publisherLabel.
            FILTER(LANG(?publisherLabel) = "en").
        }}
    }}
    GROUP BY ?item ?itemLabel ?article ?titleLabel ?publicationDateLabel
    LIMIT {search_page_num}
    OFFSET {search_offset}
    """

    sparql_wikidata = AsyncSparqlWrapper(WIKIDATA_SPARQL_URL)
    sparql_wikidata.addCustomHttpHeader("User-Agent", "game_tracker (hyobin90@gmail.com)")
    sparql_wikidata.setQuery(query_game)
    sparql_wikidata.setReturnFormat(JSON)
    result = await sparql_wikidata.asyncQuery()
    response_code = result.response.getcode()

    if response_code == 200:
        return result.convert()
    
    elif response_code == 429:
        raise RuntimeError('Too many requests 429 from Wikidata')


def _make_cadidate_list(sparql_response) -> List[Dict[str, str]]:
    ''' Makes a list of metadata of found games as candidates for the user to choose as a target game.

    Args:
        sparql_response : The response of SPARQL query containing probably multiple pages of games.

    Returns:
        candidates : A list of dictionaries containing multiple games' metadata.
    '''
    wikipedia_link = ''  # article
    wikidata_link = ''  # item
    genres = ''  # genres
    developers = ''  # developers
    publishers = ''  # publishers
    release_date = ''  # publicationDates
    platforms = ''  # platforms
    title = ''  # titleLabel

    # target_keys = ['article', 'item', 'genres', 'developers', 'publishers', 
    #                'publicationDateLabel', 'platforms', 'titleLabel']
    target_keys = ['article', 'item', 'titleLabel']

    game_candiates: List[Dict[str, str]] = []

    for element in sparql_response['results']['bindings']:  # -> List of Dicts, `element` is a dict
        if all(key in element for key in target_keys):  # Lower the level of detail here
            wikipedia_link = element['article']['value']
            wikidata_link = element['item']['value']
            genres = element['genres']['value']
            developers = element['developers']['value']
            publishers = element['publishers']['value']
            release_date = element['publicationDateLabel']['value']
            platforms = element['platforms']['value']
            title = element['titleLabel']['value']

            candiate = {
                'wikipedia_link': wikipedia_link,
                'wikidata_link': wikidata_link,
                'genres': genres,
                'developers': developers,
                'publishers': publishers,
                'release_date': release_date,
                'platforms': platforms,
                'title': title
            }

            game_candiates.append(candiate)

    return game_candiates


async def _display_game_candidates(game_candidates: List[Dict[str, str]], search_title: str, search_page_num: int, search_offset: int) -> Dict[str, str]:
    """Displays found candidates to the user to choose.
    
    Args:
      game_candiates: A list of dictionaries containing games found in `WikiData`.
      search_title: A string used to search for the game.
      search_page_num: The number of elements in `Wikidata` to be grabbed while searching.
      search_offset: The number of elements to be ignored. This is only used when the search with the same `search_title` is requested again. 
    
    Returns:
      A dictionary of selected game.
    """
    # Create a table to display
    temp = []
    for index, candidate in enumerate(game_candidates):
        temp.append({'index': index + 1, 'title': candidate.get('title'), 'platforms': candidate.get('platforms'), 'release_date': candidate.get('release_date')[:10]})

    print('Choose the desired game from the list.')
    print(tabulate(temp, headers='keys', tablefmt='rounded_outline'))

    while True:
        while True:
            try:
                choice = int(input('Enter the number of the game that you want.\nIf the desired is not present in the list, press 0.\n'))
            except ValueError as e:
                print('Please enter a valid number.\nIf the desired is not present in the list, press 0.\n')
                continue
            break
        if choice == 0:
            new_search_title = input('Put the title of the game.\n')
            if search_title == new_search_title:
              search_offset = search_offset + search_page_num # if the search is requested with the same title, the next page should be provided.
            await create_target_game_entry(search_title, search_page_num, search_offset) # TODO this part might create an infinite loop.
        elif 1 <= choice <= len(temp):
            print(f'You selected {temp[choice-1]["title"]} of {temp[choice-1]["release_date"]}')
            return game_candidates[choice-1]


def _create_game_entry(selected_candidate: Dict[str, str]) -> Game:
    """Creates an instance of `Game` class.
    
    Args:
      selected_candidated: A list of dictionaries of metadata retrieved from `Wikidata`.
      use_wikidata: If false, the metadata of the game is left empty.

    Returns:
      An instance of Game.
    """
    game_of_interest: Game = None
    title = ''
    purchase_date = ''
    play_platform = ''
    expectation = ''
    use_wikidata = False

    if selected_candidate:
        title = selected_candidate.get('title')
        use_wikidata = True
    else:
        print('The game cannot be found in `WikiData` for its metadata now.\nCreate the entry manually. Missing details can be filled up later.')
        title = input('Please enter the game\'s full title.')

    while True:
        purchase_date = input('Please put the date of purchase in the following format, yyyy-mm-dd.\n')
        if not re.match(date_pattern, purchase_date):
            print(f'Wrong date format: {purchase_date}')
            continue
        break

    while True:
        play_platform = input('Please put the device you play this game on between PS4 and PS5.\n')
        if play_platform not in ('PS4', 'PS5'):
            print(f'Wrong platform: {play_platform}')
            continue
        break

    while True:
        try:
            expectation = int(input('Please put your expectation on this game from 0 to 3, the higher, the more hyped.\n'))
            if (expectation > 3) or (expectation < 0):
                print(f'Invalid value for the expectation: {expectation}')
                continue
            break
        except ValueError:
            print(f'Please enter a valid integer.')
            continue

    game_of_interest = Game(title, purchase_date, play_platform, expectation, use_wikidata, selected_candidate)

    return game_of_interest