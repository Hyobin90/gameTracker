from aiomysql import connect, create_pool, DictCursor, OperationalError, ProgrammingError, IntegrityError
from async_sparql_wrapper import AsyncSparqlWrapper
from dotenv import load_dotenv
import os
from typing import Any, Dict, Tuple, Optional
from SPARQLWrapper import JSON

# load the credential for the DB
load_dotenv()

local_db_host = 'localhost'
local_db_port = int(os.getenv('LOCAL_SQL_DB_PORT'))
local_db_user = os.getenv('LOCAL_SQL_DB_USER')
local_db_passwd = os.getenv('LOCAL_SQL_PASSWD')
game_db_schema_path = os.path.join(os.getcwd(), 'DB', 'game_db_schema.sql')

# for Wikidata
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

async def create_db(host: str, port: int, user: str, passwd: str, db_name: str, schema_path: str):
    """Creates a database from a schema file.
    Args:
        schema_path: the path to .sql file containg the shcema.
    """
    try:
        db_connection = await connect(host=host, user=user, password=passwd, db=db_name, port=port)

        async with db_connection.cursor() as db_cursor:
            with open(schema_path, 'r') as f:
                schema = f.read()
                await db_cursor.execute(schema)
            print(f'{db_name} has been created successfully.')

    except OperationalError as e:
        print(f'Error occurred while creating DB: {e}')
        print(f'Creating a new DB, {db_name}')
        db_connection = await connect(host=host, user=user, password=passwd, port=port)
        async with db_connection.cursor() as db_cursor:
            await db_cursor.execute(f'CREATE DATABASE {db_name}')
            await db_cursor.execute(f'USE {db_name}')
            await create_db(local_db_host, local_db_port, local_db_user, local_db_passwd, 'game_db', game_db_schema_path)
    except ProgrammingError as e:
        print(f'Error occurred while creating DB: {e}')
    except Exception as e:
        raise Exception(f'Error occurred in `create_db()`: {e}') from e


async def init_pool(host: str, port: int, user: str, passwd: str, db_name: str):
    """Initializes the pool of Connection."""
    pool = await create_pool(host=host, port=port, user=user, password=passwd)
    return pool


async def query_db_with_pool(pool, query_type: str, query: str, values: Optional[Tuple] = None) -> Optional[Any]:
    """Sends a query to DB using Connection pool."""
    try:
        async with pool.acquire() as db_connection:
            async with db_connection.cursor(DictCursor) as db_cursor:
                if values:
                    await db_cursor.execute(query, values)
                else:
                    await db_cursor.execute(query)
                if query_type == 'SELECT':
                    result = await db_cursor.fetchall()
                    return result
                elif query_type in ('INSERT', 'UPDATE', 'USE'):
                    await db_connection.commit()
    except IntegrityError as e:
        raise IntegrityError() from e
    except Exception as e:
        raise RuntimeError(f'Error occurred while querying | {type(e)} : {e}') from e


async def query_wikidata(query_template: str, values: Dict) -> Any:
    """Sends SPARQL query to `Wikidata`.
    
    Args:
        query_template: the query template to be sent.
        values: A dictionary holding the parameterized values for the query.
        search_page_num: the number of elements checked per search, default to 10. This should be included in the query template
        search_offset: The number of results to skip from the beginning of the query result set,
                             in case the desired game is not found and this method is called again.
                             This should be included in the query template.

    Returns:
        the response in JSON format

    Raises:
        RuntimeError: if the response code is either 429 or 500.
    """
    query = query_template.format(**values)

    sparql_wikidata = AsyncSparqlWrapper(WIKIDATA_SPARQL_URL)
    sparql_wikidata.addCustomHttpHeader("User-Agent", "game_tracker (hyobin90@gmail.com)") # TODO store the project info somewhere else
    sparql_wikidata.setQuery(query)
    sparql_wikidata.setReturnFormat(JSON)
    result = await sparql_wikidata.asyncQuery()
    response_code = result.response.getcode()

    if response_code == 200:
        return result.convert()
    
    elif response_code == 429:
        raise RuntimeError('Too many requests 429 from Wikidata.')
    
    elif response_code == 500:
        raise RuntimeError('Timeout from Wikidata.')
