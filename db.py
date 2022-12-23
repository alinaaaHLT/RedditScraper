import time

from peewee import IntegerField, TextField, TimestampField
from playhouse.signals import Model, pre_save
from playhouse.sqlite_ext import JSONField
from playhouse.sqliteq import SqliteQueueDatabase

db = SqliteQueueDatabase('bot-db.sqlite3', pragmas={'journal_mode': 'wal', 'foreign_keys': 1})


class Thing(Model):
	# This table is not meant to represent a complete relationship of submissions/comments on reddit

	# Its behaviour is more of a log to track submissions and comments
	# that have had replies attempted and prevent replying twice

	# It also acts as a job queue of sorts, for the model text generator daemon

	# timestamp representation of when this record was entered into the database
	created_utc = TimestampField(default=time.time, utc=True)
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

	class Meta:
		database = db


def create_db_tables():

	db.create_tables(models=[Thing])
	# these stop/start calls are required
	# because of nuance in SqliteQueueDatabase
	time.sleep(0.1)
	db.stop()
	db.start()
