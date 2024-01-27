import logging
import os
import datetime
import configparser
import pymysql
import csv

import sys


def main(username):
    config = configparser.ConfigParser()
    config.read('sql_conf.ini')

    mysql_config = {
        'host': config['mysql']['host'],
        'port': int(config['mysql']['port']),
        'user': config['mysql']['user'],
        'password': config['mysql']['password'],
        'database': config['mysql']['database'],
        'charset': config['mysql']['charset']
    }
    #While True here:

    current_month = datetime.datetime.now().strftime('%B')
    current_day = datetime.datetime.now().strftime('%d')
    current_year = datetime.datetime.now().strftime('%Y')

    export_folder = f"csv_export"
    folder_string = f"{export_folder}/{current_year}/{current_month}"
    day = int(current_day) -1


    #check_and_write_last_month(mysql_config, folder_string)
    if not os.path.exists(f"{export_folder}"):
        os.mkdir(f"{export_folder}")
    if not os.path.exists(f"{export_folder}/{current_year}/"):
        os.mkdir(f"{export_folder}/{current_year}/")
    if not os.path.exists(folder_string):
        os.mkdir(folder_string)

    day_test = int(current_day)-10
    while day >= (day_test):
        path = f"{folder_string}/day_{int(day_test)}.csv"
        if os.path.exists(path):
            #logging.info("Day already exists")
            0==0
        else:
            if int(datetime.datetime.now().hour) < 3 or int(datetime.datetime.now().hour) >= 1:
                check_and_write_yesterday(mysql_config, folder_string, day)
        day = day - 1

    if os.path.exists(f"{folder_string}/{current_month}.cvs"):
        logging.info("Month csv already exists")
    else:
        0==0
        #check_and_write_last_month(mysql_config, folder_string)


def check_and_write_yesterday(mysql_config, folder_string, day):
    yesterday_start = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), datetime.time.min)
    yesterday_end = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), datetime.time.max)

    connection = pymysql.connect(**mysql_config)
    # Create a cursor object
    if os.path.exists(f"{folder_string}/{day}"):
        logging.info("Day already exists")
    else:
        try:
            with connection.cursor() as cursor:
                # SQL query using placeholders for dates
                query = """
                SELECT *
                FROM bot_db
                WHERE datetime BETWEEN %s AND %s
                """

                # Execute the query with the date parameters
                cursor.execute(query, (yesterday_start, yesterday_end))

                # Fetch the results
                results = cursor.fetchall()

                # Process the results
                for row in results:
                    print(row)
                csv_file_name = f"{folder_string}/day_{int(day)-1}.csv"
                fp = open(csv_file_name, 'w', encoding="utf-8")
                csv_file = csv.writer(fp)
                csv_file.writerows(results)
                fp.close()
                x = 0

        finally:
            # Close the connection
            connection.close()


def check_and_write_last_month(mysql_config, folder_string):
    last_month_start = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), datetime.time.min)
    last_month_end = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), datetime.time.max)

    connection = pymysql.connect(**mysql_config)
    # Create a cursor object
    current_month = datetime.datetime.now().strftime('%B')
    if os.path.exists(f"{folder_string}/{current_month}"):
        logging.info("Day already exists")
    else:
        try:
            with connection.cursor() as cursor:
                # SQL query using placeholders for dates
                query = """
                    SELECT *
                    FROM bot_db
                    WHERE datetime BETWEEN %s AND %s
                    """

                # Execute the query with the date parameters
                cursor.execute(query, (last_month_start, last_month_end))

                # Fetch the results
                results = cursor.fetchall()

                # Process the results
                for row in results:
                    print(row)
                csv_file_name = f"{folder_string}/day_2.csv"
                fp = open(csv_file_name, 'w', encoding="utf-8")
                csv_file = csv.writer(fp)
                csv_file.writerows(results)
                fp.close()
                x = 0

        finally:
            # Close the connection
            connection.close()


if __name__ == '__main__':
    main("e")
