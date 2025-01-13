import asyncio
from typing import List
from SPARQLWrapper import JSON
from async_sparql_wrapper import AsyncSparqlWrapper


class Game():
  def __init__(self, wikipiedia_link:str, wikidata_link:str, 
               genres:str, developers:str, publishers:str,
               release_date:str, platforms:str, title:str):
    self.wikipedia_link = wikipiedia_link
    self.wikidata_link = wikidata_link
    self.genres = genres
    self.developers = developers
    self.publishers = publishers
    self.release_date = release_date
    self.platforms = platforms
    self.title = title


search_keyword = 'god of war'
wikidata_sparql_url = "https://query.wikidata.org/sparql"
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
  FILTER(CONTAINS(LCASE(?label), "{search_keyword}")).
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
LIMIT 10
"""
headers = {
    'Accept': 'application/json'  # Force JSON response
}

params = {
    'query': query_game,
    'format': 'application/json'  # Ensure JSON format in query string
}

# TODO still there are items with empty value or non ps4 or ps5
async def test():
  sparql_wikidata = AsyncSparqlWrapper(wikidata_sparql_url)
  sparql_wikidata.setQuery(query_game)
  sparql_wikidata.setReturnFormat(JSON)
  response = await sparql_wikidata.asyncQueryAndConvert()

  wikipedia_link = '' # article
  wikidata_link = '' # item
  genres = '' # genres
  developers = '' # developers
  publishers = '' # publishers
  release_date = '' # publicationDates # TODO find a way to tell dates per platform
  platforms = '' # platforms
  title = '' # titleLabel

  target_keys = ['article', 'item', 'genres', 'developers', 'publishers', 
                 'publicationDates', 'platforms', 'titleLabel']
  
  game_candiates: List[Game] = []

  for element in response['results']['bindings']: # -> List of Dicts, `element` is a dict
    if all(key in element for key in target_keys):
      wikipedia_link = element['article']['value']
      wikidata_link = element['item']['value']
      genres = element['genres']['value']
      developers = element['developers']['value']
      publishers = element['publishers']['value']
      release_date = element['publicationDates']['value']
      platforms = element['platforms']['value']
      title = element['titleLabel']['value']
      candiate = Game(wikipedia_link, wikidata_link, genres, developers, publishers, release_date, platforms, title)
      game_candiates.append(candiate)

  return game_candiates

game_candiates = asyncio.run(test())
for candiate in game_candiates:
  print(vars(candiate))
  
 




    



# TODO date without time
# while True:
#   search_keyword = input('Put the title of the game.\n')
  
#   sparql_wikidata = SPARQLWrapper(wikidata_sparql_url)
#   sparql_wikidata.setQuery(query_game)
#   sparql_wikidata.setReturnFormat(JSON)
  
#   try:
#     wikidata_query_result = sparql_wikidata.query()
#     results = wikidata_query_result.convert()

#     bindings  = results['results']['bindings']
#     for binding in bindings:
#       title = binding['titleLabel']['value']
#       print(title)
#   #TODO EndPointInternalError, status code 500
#   except SPARQLExceptions as e:
#     print(f'Error occurrred : {e}')
#     search_keyword = input('Put the title of the game.\n')
#     # how to make it loop?
#   # TODO narrow down the range of exceptions
#   except Exception as e:
#     response_code = wikidata_query_result.response.getcode()
#     if response_code == 429:
#       print('too many requests')

# #TODO Too many requests, status code 429
# TODO have the user to input the search keyword
# TODO multiple cases are retrieve, have the user choose the game
