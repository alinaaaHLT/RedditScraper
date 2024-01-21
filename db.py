
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
    'database': config['mysql']['database']
}

# Establishing MySQL database connection
db = MySQLDatabase(**mysql_config)

class bot_db(Model):
    # The rest of the class remains the same as it was in the original file

	# This table is not meant to represent a complete relationship of submissions/comments on reddit

	# Its behaviour is more of a log to track submissions and comments
	# that have had replies attempted and prevent replying twice

	# It also acts as a job queue of sorts, for the model text generator daemon

	# timestamp representation of when this record was entered into the database
	datetime =  DateTimeField(default=datetime.datetime.now)
	status = IntegerField(default=1)

	# the praw *name* of the original comment or submission,
	# where t3_ prefix = submission, t1_ = comment, t4_ = message
	source_name = TextField()

	# Author of the post (Redditor's username)
	author = TextField()
	# Shortlink to comment/post
	link = TextField()
	#Title of a Submission
	title = TextField(null=True)
	# Body of Submission/Comment
	body = TextField(null=True)
	removal_reason = TextField(null=True)
	id = TextField(null=False)

	class Meta:
		database = db


def create_db_tables():

	db.create_tables(models=[bot_db])
	# these stop/start calls are required
	# because of nuance in SqliteQueueDatabase
	time.sleep(0.1)
