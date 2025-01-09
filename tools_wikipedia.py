import datetime
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
import pprint



search_keyword = 'space marine 2'
wikidata_sparql_url = "https://query.wikidata.org/sparql"
query_game = f"""
SELECT DISTINCT ?item ?itemLabel ?article ?title ?genre ?developer ?publisher
WHERE {{
  ?item wdt:P31 wd:Q7889;
        rdfs:label ?label. 
  FILTER(CONTAINS(LCASE(?label), "{search_keyword}"))
  OPTIONAL {{
    ?article schema:about ?item;
             schema:inLanguage "en";  # English articles
             schema:isPartOf <https://en.wikipedia.org/>.
  }}
  OPTIONAL {{
    ?item wdt:P1476 ?title
  }}
  OPTIONAL {{
    ?item wdt:P136 ?genre
  }}
  OPTIONAL {{
    ?item wdt:P178 ?developer
  }}
  OPTIONAL {{
    ?item wdt:P123 ?publisher
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 5
"""

sparql_wikidata = SPARQLWrapper(wikidata_sparql_url)
sparql_wikidata.setQuery(query_game)
sparql_wikidata.setReturnFormat(JSON)

# TODO retrieve the link
pprint.pprint(sparql_wikidata.query().convert())


def later():
  today = datetime.datetime.now()
  date = today.strftime('%Y/%m/%d')


  # TODO search_keyword should be provided in small letters


  # headers = {
  #     "Accept": "application/json"
  # }

  # params = {
  #     "query": sparql_query
  # }

  wikidata_response = requests.get(wikidata_url, headers=headers, params=params)
  print(wikidata_response)
  ##data = wikidata_response.json()

  ##pprint.pprint(data)