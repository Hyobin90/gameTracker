from aiomysql import connect, create_pool, OperationalError, ProgrammingError
from dotenv import load_dotenv
import os
from typing import Any, Optional


# load the credential for the DB
load_dotenv()

local_db_host = 'localhost'
local_db_port = int(os.getenv('LOCAL_SQL_DB_PORT'))
local_db_user = os.getenv('LOCAL_SQL_DB_USER')
local_db_passwd = os.getenv('LOCAL_SQL_PASSWD')
game_db_schema_path = os.path.join(os.getcwd(), 'DB', 'game_db_schema.sql')

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
        print(f'Error occurred : {e}')
        print(f'Creating a new DB, {db_name}')
        db_connection = await connect(host=host, user=user, password=passwd, port=port)
        async with db_connection.cursor() as db_cursor:
            await db_cursor.execute(f'CREATE DATABASE {db_name}')
            await db_cursor.execute(f'USE {db_name}')
            await create_db(local_db_host, local_db_port, local_db_user, local_db_passwd, 'game_db', game_db_schema_path)
    except ProgrammingError as e:
        print(f'Error occurred : {e}')


async def init_pool(host: str, port: int, user: str, passwd: str, db_name: str):
    """Initializes the pool of Connection."""
    pool = await create_pool(host=host, port=port, user=user, password=passwd)
    return pool


async def query_db_with_pool(pool, query) -> Optional[Any]:
    """Sends a query to DB using Connection pool."""
    try:
        async with pool.acquire() as db_connection:
            async with db_connection.cursor() as db_cursor:
                await db_cursor.execute(query)
                result = db_cursor.fetchall()
                return result
    except Exception as e:
        print(f'Error occurred while querying : {e}')