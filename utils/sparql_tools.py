"""Scripts that holds methods using SPARQL for Wikidata"""
from server.models.mysqldb import query_wikidata
from typing import Any, Dict, List

async def search_wikidata(search_title, search_page_num, search_offset) -> Any:
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


def make_cadidate_list_wikidata(sparql_response) -> List[Dict[str, str]]:
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


async def get_metadata_from_wikidata(wikidata_code: str) -> Dict[str, str]:
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
