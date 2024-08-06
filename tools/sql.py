# connect to local postgresql database
import psycopg2
from langchain_core.tools import Tool
from langchain_core.pydantic_v1 import BaseModel
from typing import List
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
database_config = config["database"]
# connect to local postgresql database
conn = psycopg2.connect(
    dbname=database_config["dbname"],
    user=database_config["user"],
    password=database_config["password"],
    host=database_config["host"],
    port=database_config["port"],
)


# fetch all tables in the database
def list_tables():
    database_name = database_config["dbname"]
    print(database_name)
    query = f"""
    SELECT table_name
    FROM  {database_name}.information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    return "\n".join(row[0] for row in rows if row[0] is not None)


# run query
def run_query(query):
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        return str(e)


# custom __arg1 from schema for the something else
class RunQueryArgsSchema(BaseModel):
    query: str


run_query_tool = Tool.from_function(
    name="run_query",
    description="Run a postgresql query",
    func=run_query,
    args_schema=RunQueryArgsSchema,
)


# describe the table
def describe_table(table_names: List[str]):
    tables = ", ".join([f"'{table}'" for table in table_names])
    query = f"""
SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_name IN ({tables});
    """
    rows = run_query(query)
    descriptions = {}
    for row in rows:
        table_name = row[0]
        column_info = f"{row[1]} {row[2]}"
        if table_name not in descriptions:
            descriptions[table_name] = []
        descriptions[table_name].append(column_info)
    return "\n".join(
        f"{table}: {', '.join(columns)}" for table, columns in descriptions.items()
    )


# more information how schema should look like
class DescribeTableArgsSchema(BaseModel):
    table_names: list[str]


describe_table_tool = Tool.from_function(
    name="describe_tables",
    description="Returns the scehma of the given tables",
    func=describe_table,
    args_schema=DescribeTableArgsSchema,
)
