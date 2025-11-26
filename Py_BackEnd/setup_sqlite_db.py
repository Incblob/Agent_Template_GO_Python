# %%
from os import path, listdir
from typing import List, Tuple
import sqlite3
import logging
from pprint import pprint

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DB_FILE = "data/sqlite/python.db"
DB_DIR = "data/sqlite"
TEXT_FILES = "data/python_wiki/"
TABLE_NAME = "Pythons"

assert path.isdir(DB_DIR), "DB dir is missing"
assert path.isdir(TEXT_FILES), "Text dir is missing"
assert len(listdir(TEXT_FILES)) > 0, "Text files missing"
# %%
sql_create_table_if_not_exists = """
        CREATE TABLE IF NOT EXISTS Pythons(
            id INTEGER PRIMARY KEY UNIQUE,
            subject text UNIQUE NOT NULL,
            text text NOT NULL
    );"""

sql_get_tables = """SELECT name from sqlite_master WHERE type='table';"""

sql_insert_data_not_dupl = """
        INSERT INTO Pythons (subject, text)
        VALUES (?, ?)
    """


def read_text_files(TEXT_FILES: str) -> List[Tuple[str, str]]:
    text_files = listdir(TEXT_FILES)
    text_read: List[Tuple[str, str]] = []
    for file in text_files:
        with open(TEXT_FILES + "/" + file) as f:
            text_read.append((file.replace(".txt", ""), f.read()))
    return text_read


# read data into db if no file
try:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # check for existing table
        tables = cursor.execute(sql_get_tables).fetchall()
        if tables:
            tables = tables[0]

        if TABLE_NAME not in tables:
            logger.info(f"{TABLE_NAME} not in DB\nexisting tables: {tables}")
            cursor.execute(sql_create_table_if_not_exists)
            logger.info(f"created {TABLE_NAME}")
            conn.commit()

        # insert data w. duplicate check on insert
        logger.info("adding text data")
        text_tuples = read_text_files(TEXT_FILES)
        for subject, text in text_tuples:
            try:
                logger.info(f'adding "{subject}" w. text\n\t{text[:20]}...')
                cursor.execute(sql_insert_data_not_dupl, (subject, text))
            except sqlite3.IntegrityError as e:
                logger.error(
                    f"Error in inserting data for {subject}:\n\t probably not a unique subject"
                )
        conn.commit()

        # insert data w. duplicate subject check before insert

except sqlite3.OperationalError as e:
    print("error with db\n\t!!!", e)
# %%
# test
# with sqlite3.connect(DB_FILE) as conn:
#     cursor = conn.cursor()
#     table_content = cursor.execute("Select * from pythons").fetchall()
#     pprint(table_content)

# %%
