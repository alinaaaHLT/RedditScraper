#!/usr/bin/env python3

import logging
import threading
import time
import difflib
from configparser import ConfigParser
from datetime import datetime, timedelta

import praw as praw
from praw.models import (Submission as praw_Submission, Comment as praw_Comment, Message as praw_Message)
from peewee import fn

from .db_mod import modlog_db as mod_log_db_Thing

import logging

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# for logger_name in ("pbfaw", "prawcore"):
#    logger = logging.getLogger(logger_name)
#    logger.setLevel(logging.DEBUG)
#    logger.addHandler(handler)
#    logger.addHandler(handler)

def start_modlog(username):
	modlog_io = ModLogIO(bot_username=username)
	modlog_io.start()

class ModLogIO(threading.Thread):
	"""
	Advised that praw can have problems with threads,
	so decided to keep all praw tasks in one daemon
	"""

	_praw = None
	_imgur_client_id = None

	_keyword_helper = None

	#sql_config = ConfigParser()
	#bot_config.read('sql_conf.ini')

	_subreddits = []
	_subreddit_flair_id_map = {}
	_new_submission_schedule = []

	def __init__(self, bot_username):
		super().__init__(name=bot_username, daemon=True)

		self._bot_username = bot_username

		self._praw = praw.Reddit(self._bot_username, timeout=64)
		self.submission_kind = 't3_'
		self.message_kind = 't4_'

	def run(self):
		subreddits_config_string = "SubSimGPT2Interactive"
		self._subreddits = [x.strip() for x in subreddits_config_string.lower().split(',')]
		# pick up incoming submissions, comments etc. from reddit and submit jobs for them
		logging.info(f"Beginning to process incoming modlog actions")
		while True:
			try:
				if self._subreddits:
					self.poll_incoming_modlog()

			except:
				logging.exception("Exception occurred while processing the incoming streams")

			time.sleep(15)

	def poll_incoming_modlog(self):

		sr = self._praw.subreddit('+'.join(self._subreddits))
		for log_thing in sr.mod.log(limit=10):  # bot.subreddit("mod").mod.log(limit=20):
			record = is_mod_action_thing_in_database(log_thing)

			if record:
				print(f"{log_thing.id} already in db")
			if not record:
				insert_mod_action_thing_into_database(log_thing)
				print(f"{log_thing.id} inserted in db")


def is_mod_action_thing_in_database(log_thing):
    # Note that this is using the prefixed reddit id, ie t3_, t1_
    # do not mix it with the unprefixed version which is called id!
    # Filter by the bot username
    record = mod_log_db_Thing.get_or_none(mod_log_db_Thing.id == log_thing.id)

    return record

def insert_mod_action_thing_into_database(log_thing):

    record_dict = {}
    record_dict['id'] = log_thing.id
    record_dict['datetime'] = datetime.fromtimestamp(log_thing.created_utc)
    record_dict['action'] = log_thing.action
    record_dict['details'] = log_thing.details
    record_dict['mod_username'] = getattr(log_thing.mod, 'name', '')
    record_dict['target_author'] = log_thing.target_author
    if log_thing.target_body is not None:
        record_dict['target_body'] = log_thing.target_body
    record_dict['target_fullname'] = log_thing.target_fullname
    record_dict['target_permalink'] = log_thing.target_permalink

    return mod_log_db_Thing.create(**record_dict)
