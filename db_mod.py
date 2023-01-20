import time

from peewee import IntegerField, TextField, TimestampField
from playhouse.signals import Model, pre_save
from playhouse.sqlite_ext import JSONField
from playhouse.sqliteq import SqliteQueueDatabase

db = SqliteQueueDatabase('mod-db.sqlite3', pragmas={'journal_mode': 'wal', 'foreign_keys': 1})


class Thing(Model):

	created_utc = TimestampField(default=time.time, utc=True)
	action = TextField()

	details = TextField(null=True)
	mod = TextField()
	target_author = TextField()
	target_body = TextField(null=True)
	id = TextField()
	target_selftext = TextField(null=True)
	target_fullname = TextField(null=True)
	target_permalink = TextField(null=True)

	class Meta:
		database = db


def create_db_tables():

	db.create_tables(models=[Thing])
	# these stop/start calls are required
	# because of nuance in SqliteQueueDatabase
	time.sleep(0.1)
	db.stop()
	db.start()
