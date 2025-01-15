"""Manage games by registering, and updating them."""
import asyncio
from async_sparql_wrapper import AsyncSparqlWrapper
from game import Game
import re
from SPARQLWrapper import JSON
from tabulate import tabulate # temp mesure for user interaction
from typing import Any, Dict, List


wikidata_sparql_url = "https://query.wikidata.org/sparql"
date_pattern = r'^\d{4}-\d{2}-\d{2}$'

def search_target_game(search_title:str, search_page_num: int = 10, search_offset:int = 0) -> Game:
    try:
        if not search_title:
            search_title = input('Put the title of the game.\n')

        response = asyncio.run(_search_games_in_metadata(search_title, search_page_num, search_offset))
        game_candidates: List[Dict[str, str]] = _make_cadidate_list(response)

        if len(game_candidates) == 0:
            search_title = input(f'Nothing has been found with {search_title}. Please try with another title.\n')
            search_target_game(search_title, search_page_num, 0) # set the offset to 0 because this is a new search

        temp = []
        temp_index = 0
        for candiate in game_candidates:
            temp_index += 1
            temp.append({'index' : temp_index, 'title' : candiate['title'], 'release_date' : candiate['release_date']})
        
        print('Choose the desired game from the list.')
        print(tabulate(temp, headers='keys', tablefmt='rounded_outline'))

        while True:
            try:
                choice = int(input('Enter the number of the game that you want.\nIf the desired is not present in the list, press 0.\n'))
                if 1 <= choice <= len(temp):
                    print(f'You selected {temp[choice-1]['title']} of {temp[choice-1]['release_date']}')
                    purchase_date = None
                    play_platform = None
                    expectation = None
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
                        except ValueError as e:
                            print(f'Please enter a valid integer.')
                            continue
                    personal_data: Dict = {'purchase_date': purchase_date, 'play_platform': play_platform, 'expectation': expectation}
                    return Game(personal_data=personal_data, wikidata=game_candidates[choice - 1]) # TODO GTPS-006 expect data other than metadata

                if choice == 0:
                    search_target_game(search_title, search_page_num, search_offset+search_page_num)
                else:
                    print(f'Please enter a valid number.')
            except ValueError as e:
                print(f'Invalid input. : {e}')

    # error catching for SPARQL query
    except Exception as e:
        print(f'Error occurred : {e}')


async def _search_games_in_metadata(search_title:str, search_page_num: int = 10, search_offset:int = 0) -> Any:
  '''Sends SPARQL query to `Metadata` for a game and returns the response.
  
  Args:
    search_title (str): A game's title to search for in `WikiData`.
    search_offset (int): The number of results to skip from the beginning of the query result set,
                         in case the desired game is not found and this method is called again.

  Returns:
    response : The response of SPARQL query containing probably multiple pages of games.

  '''
  query_game = f"""
  SELECT DISTINCT ?item ?itemLabel ?article ?titleLabel
        (GROUP_CONCAT(DISTINCT ?genreLabel; separator=", ") AS ?genres)
        (GROUP_CONCAT(DISTINCT ?developerLabel; separator=", ") AS ?developers)
        (GROUP_CONCAT(DISTINCT ?publisherLabel; separator=", ") AS ?publishers)
        (GROUP_CONCAT(DISTINCT ?publicationDateLabel; separator=", ") AS ?publicationDates)
        (GROUP_CONCAT(DISTINCT ?platformLabel; separator=", ") AS ?platforms)
  WHERE {{
    ?item wdt:P31 wd:Q7889;
          rdfs:label ?label.
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
      ?item wdt:P577 ?publicationDateLabel.
    }}
      OPTIONAL {{
      ?item wdt:P400 ?platform.
      ?platform rdfs:label ?platformLabel.
      FILTER(LANG(?platformLabel) = "en").
      FILTER(CONTAINS(LCASE(?platformLabel), "playstation 4") || CONTAINS(LCASE(?platformLabel), "playstation 5")).

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
  GROUP BY ?item ?itemLabel ?article ?titleLabel
  LIMIT {search_page_num}
  OFFSET {search_offset}
  """

  sparql_wikidata = AsyncSparqlWrapper(wikidata_sparql_url)
  sparql_wikidata.setQuery(query_game)
  sparql_wikidata.setReturnFormat(JSON)
  result = await sparql_wikidata.asyncQuery()
  response_code = result.response.getcode()

  if response_code == 200:
    return result.convert()
  
  elif response_code == 429:
    raise RuntimeError('Too many requests 429 from Wikidata')


def _make_cadidate_list(sparql_response) -> List[Dict[str, str]]:
  ''' Makes a list of metadata of found games as cadidates for the user to choose as a target game.

  Args:
    sparql_response : The response of SPARQL query containing probably multiple pages of games.

  Returns:
    candiates : A list of dictionaries containing multiple games' metadata.
  '''
  wikipedia_link = '' # article
  wikidata_link = '' # item
  genres = '' # genres
  developers = '' # developers
  publishers = '' # publishers
  release_date = '' # publicationDates
  platforms = '' # platforms
  title = '' # titleLabel

  target_keys = ['article', 'item', 'genres', 'developers', 'publishers', 
                 'publicationDates', 'platforms', 'titleLabel']
  
  game_candiates: List[Dict[str, str]] = []

  for element in sparql_response['results']['bindings']: # -> List of Dicts, `element` is a dict
    if all(key in element for key in target_keys):
      wikipedia_link = element['article']['value']
      wikidata_link = element['item']['value']
      genres = element['genres']['value']
      developers = element['developers']['value']
      publishers = element['publishers']['value']
      release_date = element['publicationDates']['value']
      platforms = element['platforms']['value']
      title = element['titleLabel']['value']

      candiate = {
        'wikipedia_link' : wikipedia_link,
        'wikidata_link' : wikidata_link,
        'genres' : genres,
        'developers' : developers,
        'publishers' : publishers,
        'release_date' : release_date,
        'platforms' : platforms,
        'title': title}

      game_candiates.append(candiate)

  return game_candiates
