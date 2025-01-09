import aiohttp
from aiohttp import client_exceptions
import asyncio
from SPARQLWrapper import SPARQLWrapper
import xmltodict
import requests
from pprint import pprint
from typing import List, Dict
from lxml import etree
from SPARQLWrapper import JSON
from async_sparql_wrapper import AsyncSparqlWrapper



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
  pprint(response)

asyncio.run(test())
# async def run_sparql_query(query, sparql_url=wikidata_sparql_url) -> List[Dict]:
#   async with aiohttp.ClientSession() as session:
#     async with session.get(sparql_url, headers=headers, params=params) as response:
#       if response.status == 200:
#         xml_data = await response.text()
#         json_data = xmltodict.parse(xml_data)
#         # TODO parse `json_data` one more time manually
#         pprint.pprint(json_data)
#         print(type(json_data['sparql']['results']['result']))
#         return json_data['sparql']['results']['result']
#       else:
#         print(f'Error {response.status} - {response.reason}')
#         raise RuntimeError(response.reason)
    

# async def process_sparql_query_result(search_keyword):
#   bindings = await run_sparql_query(query=query_game)

#   for binding in bindings:
#     title = binding['binding']['@name']
#     print(f'title : {title}')


# asyncio.run(process_sparql_query_result(search_keyword))
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
