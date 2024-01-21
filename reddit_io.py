#!/usr/bin/env python3

import logging
import threading
import time
import difflib
from configparser import ConfigParser
from datetime import datetime, timedelta

import pbfaw as pbfaw
import praw as praw
from praw.models import (Submission as praw_Submission, Comment as praw_Comment, Message as praw_Message)
from peewee import fn

import db
from db import bot_db as db_Thing
from db_mod import modlog_db as mod_log_db_Thing

import logging

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

kw_list = ['aryan', 'assassin', 'auschwitz', 'behead', 'black people', 'bomb', 'child porn', 'chink', 'clinton',
           'columbine', 'concentration camp', 'cunt', 'dago', 'death', 'decapitat', 'dies', 'died', 'drown',
           'execution', 'fag', 'fuck off', 'fuck you', 'genocide', 'hitler', 'holocaust', 'incest', 'isis', 'israel',
           'jewish', 'jews', 'jihad', 'kike', 'kill', 'kkk', 'kys', 'loli', 'master race', 'murder', 'nationalist',
           'nazi', 'nigga', 'nigger', 'paedo', 'paki', 'palestin', 'pedo', 'racist', 'rape', 'raping', 'rapist',
           'retard', 'school shoot', 'self harm', 'shoot', 'stab', 'slut', 'spic', 'suicide', 'swastika', 'terroris',
           'torture', 'tranny', 'trump', 'white power', 'you die']
# Keyword list from Automod

# for logger_name in ("pbfaw", "prawcore"):
#    logger = logging.getLogger(logger_name)
#    logger.setLevel(logging.DEBUG)
#    logger.addHandler(handler)

class RedditIO(threading.Thread):
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
		subreddits_config_string = ['SubSimGPT2Interactive']
		#self._subreddits = [x.strip() for x in subreddits_config_string.lower().split(',')]
		# pick up incoming submissions, comments etc. from reddit and submit jobs for them
		logging.info(f"Beginning to process incoming reddit streams")
		while True:
			try:
				if self._subreddits:
					self.poll_incoming_streams()
					self.sync_modlog_to_discord()

			except:
				logging.exception("Exception occurred while processing the incoming streams")

			time.sleep(2)

	def poll_incoming_streams(self):

		# Setup all the streams for new comments and submissions
		sr = self._praw.subreddit('+'.join(self._subreddits))
		submissions = sr.stream.submissions(pause_after=0)
		comments = sr.stream.comments(pause_after=0)

		# Merge the streams in a single loop to DRY the code
		for praw_thing in chain_listing_generators(submissions, comments):

			if isinstance(praw_thing, dict):
				praw_thing = self._praw.submission(url=praw_thing["data"]["permalink"])

			# Check in the database to see if it already exists
			record = self.is_praw_thing_in_database(praw_thing)

			# If the thing is already in the database then we've already calculated a reply for it.
			if not record:
				thing_label = 'comment' if isinstance(praw_thing, pbfaw_Comment) or isinstance(praw_thing,
																							   praw_Comment) else 'submission'
				logging.info(f"New {thing_label} thing received {praw_thing.name} from {praw_thing.subreddit}")

				# insert it into the database
				self.insert_praw_thing_into_database(praw_thing)

	def sync_modlog_to_discord(self):

		sr = self._praw.subreddit('+'.join(self._subreddits))
		for log_thing in sr.mod.log(limit=50):  # bot.subreddit("mod").mod.log(limit=20):
			record = is_mod_action_thing_in_database(log_thing)

			if record:
				print(f"{log_thing.id} already in db")
			if not record:
				insert_mod_action_thing_into_database(log_thing)
	def is_praw_thing_in_database(self, praw_thing):
		# Note that this is using the prefixed reddit id, ie t3_, t1_
		# do not mix it with the unprefixed version which is called id!
		# Filter by the bot username
		record = db_Thing.get_or_none(db_Thing.source_name == self._get_name_for_thing(praw_thing))

		return record

	def _get_name_for_thing(self, praw_thing):
		# Infer the name for the thing without doing a network request
		if isinstance(praw_thing, pbfaw_Comment) or isinstance(praw_thing, praw_Comment):
			return f"t1_{praw_thing.id}"
		if isinstance(praw_thing, pbfaw_Submission) or isinstance(praw_thing, praw_Submission):
			return f"{self.submission_kind}{praw_thing.id}"
		if isinstance(praw_thing, pbfaw_Message) or isinstance(praw_thing, praw_Message):
			return f"{self.message_kind}{praw_thing.id}"

	def insert_praw_thing_into_database(self, praw_thing):

		record_dict = {}
		record_dict['source_name'] = praw_thing.name
		record_dict['created_utc'] = praw_thing.created_utc
		record_dict['author'] = getattr(praw_thing.author, 'name', '')
		record_dict['link'] = praw_thing.permalink
		record_dict['id'] = praw_thing.id
		test = praw_thing.fullname[:3]
		if praw_thing.fullname[:3] == 't3_':
			record_dict['title'] = praw_thing.title
			if praw_thing.selftext:
				record_dict['body'] = praw_thing.selftext
			else:
				record_dict['body'] = praw_thing.url
		if praw_thing.fullname[:3] == 't1_':
			record_dict['body'] = praw_thing.body
		return db_Thing.create(**record_dict)

	def _is_praw_thing_removed_or_deleted(self, praw_thing):

		if praw_thing.author is None:
			logging.error(f'{praw_thing} has been deleted.')
			return True

		submission = None

		if isinstance(praw_thing, pbfaw_Message) or isinstance(praw_thing, praw_Message):
			# A message that has been deleted can't be retrieved due to bug in praw
			return False

		elif isinstance(praw_thing, pbfaw_Comment) or isinstance(praw_thing, praw_Comment):
			submission = praw_thing.submission

			if praw_thing.body in ['[removed]', '[deleted]']:
				logging.error(f'Comment {praw_thing} has been deleted.')
				return True

		elif isinstance(praw_thing, pbfaw_Submission) or isinstance(praw_thing, praw_Submission):
			submission = praw_thing

		if submission:
			if submission.author is None or submission.removal_reason is not None:
				logging.error(f'Submission {submission} has been removed or deleted.')
				return True

			if submission.locked:
				logging.error(f'Submission {submission} has been locked.')
				return True
		# Assume not deleted
		return False

	def _check_reply_matches_history(self, source_praw_thing, reply_body, to_level=6):
		# Checks through the history of the source_praw_thing
		# and if the reply_body has a high match, return False.

		counter = 0
		text_to_compare = ''
		loop_thing = source_praw_thing
		break_after_compare = False

		while loop_thing and counter < to_level:
			if isinstance(loop_thing, pbfaw_Submission) or isinstance(loop_thing, praw_Submission):
				# On a submission we'll only check the title
				text_to_compare = loop_thing.title
				break_after_compare = True

			elif isinstance(loop_thing, pbfaw_Comment) or isinstance(loop_thing, praw_Comment):
				text_to_compare = loop_thing.body
				loop_thing = loop_thing.parent()

			elif isinstance(loop_thing, pbfaw_Message) or isinstance(loop_thing, praw_Message):
				text_to_compare = loop_thing.body

				if loop_thing.parent_id:
					loop_thing = self._praw.inbox.message(message_id=loop_thing.parent_id[3:])
				else:
					# It's the top message
					break_after_compare = True

			match_rate = difflib.SequenceMatcher(None, text_to_compare.lower(), reply_body.lower()).ratio()
			if difflib.SequenceMatcher(None, text_to_compare.lower(), reply_body.lower()).ratio() >= 0.95:
				# A historical asset and the reply are > 95% match, return True
				return True

			counter += 1

			if break_after_compare:
				break

		return False


def chain_listing_generators(*iterables):
	# Special tool for chaining PRAW's listing generators
	# It joins the three iterables together so that we can DRY
	for it in iterables:
		for element in it:
			if element is None:
				break
			else:
				yield element

def is_mod_action_thing_in_database(log_thing):
    # Note that this is using the prefixed reddit id, ie t3_, t1_
    # do not mix it with the unprefixed version which is called id!
    # Filter by the bot username
    record = mod_log_db_Thing.get_or_none(mod_log_db_Thing.id == log_thing.id)

    return record

def insert_mod_action_thing_into_database(log_thing):
    # Put the mod action into the db, lazily stolen from ssi-bot
    record_dict = {}
    record_dict['id'] = log_thing.id
    record_dict['created_utc'] = log_thing.created_utc
    record_dict['action'] = log_thing.action
    record_dict['details'] = log_thing.details
    record_dict['mod_username'] = getattr(log_thing.mod, 'name', '')
    record_dict['target_author'] = log_thing.target_author
    if log_thing.target_body is not None:
        record_dict['target_body'] = log_thing.target_body
    record_dict['target_fullname'] = log_thing.target_fullname
    record_dict['target_permalink'] = log_thing.target_permalink

    return mod_log_db_Thing.create(**record_dict)