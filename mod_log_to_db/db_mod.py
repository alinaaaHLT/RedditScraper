import configparser
import time
from peewee import *
from playhouse.signals import pre_save
from playhouse.mysql_ext import MySQLDatabase, JSONField
import datetime

# Reading MySQL configuration from sql_conf.ini
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

# Establishing MySQL database connection
db = MySQLDatabase(**mysql_config)


class modlog_db(Model):
    created_utc = TimestampField(default=time.time, utc=True)
    action = TextField()

    details = TextField(null=True)
    mod_username = TextField()
    target_author = TextField()
    target_body = TextField(null=True)
    id = TextField(255)
    target_selftext = TextField(null=True)
    target_fullname = TextField(null=True)
    target_permalink = TextField(null=True)
    posted = BooleanField(null=False)

    class Meta:
        database = db


def create_db_tables():
    db.create_tables(models=[modlog_db])
    # these stop/start calls are required
    # because of nuance in SqliteQueueDatabase
    time.sleep(0.1)
