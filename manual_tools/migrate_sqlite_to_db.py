import sqlite3
import pymysql
import configparser
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

# SQLite connection
sqlite_conn = sqlite3.connect('bot-db.sqlite3')  # Update the path to your SQLite DB
sqlite_cursor = sqlite_conn.cursor()

config = configparser.ConfigParser()
config.read('../sql_conf.ini')

mysql_config = {
    'host': config['mysql']['host'],
    'port': int(config['mysql']['port']),
    'user': config['mysql']['user'],
    'password': config['mysql']['password'],
    'database': config['mysql']['database'],
    'charset': config['mysql']['charset']
}

# MySQL connection
mysql_conn = pymysql.connect(**mysql_config)
mysql_cursor = mysql_conn.cursor()


def row_exists(cursor, source_name, id):
    source_name = source_name.split("_")[1]
    query = "SELECT EXISTS(SELECT 1 FROM bot_db WHERE id = %s LIMIT 1)"
    cursor.execute(query, (id))
    return cursor.fetchone()[0]


# Read from SQLite and Insert into MySQL
try:
    sqlite_cursor.execute(
        "SELECT created_utc, status, source_name, author, link, title, body FROM thing")  # Update the table name
    i = 0
    l = 0
    for row in sqlite_cursor.fetchall():
        created_utc, status, source_name, author, link, title, body = row

        id = source_name.split("_")[1]
        # Check if the row already exists in MySQL
        # if test == 1:
        # break
        if not row_exists(mysql_cursor, source_name, id):
            created_utc, status, source_name, author, link, title, body = row
            datetime = datetime.fromtimestamp(created_utc)
            mysql_insert_query = """INSERT INTO bot_db (datetime, source_name, status, id, author, link, title, body) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""  # Update the table and column names
            mysql_cursor.execute(mysql_insert_query, (datetime, source_name, status, id, author, link, title, body))
            logging.info(f"Inserted:   {row}")
            i = i + 1
            l = l + 1

        else:
            logging.info(f"Skipped:   {row} ")

        if i % 10 == i >= 1:
            mysql_conn.commit()
            logging.info(f"commited: {i}, total {l}")
            i = 0

    mysql_conn.commit()

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()
