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

kw_list = ['aryan', 'assassin', 'auschwitz', 'behead', 'black people', 'bomb', 'child porn', 'chink', 'clinton',
           'columbine', 'concentration camp', 'cunt', 'dago', 'death', 'decapitat', 'dies', 'died', 'drown',
           'execution', 'fag', 'fuck off', 'fuck you', 'genocide', 'hitler', 'holocaust', 'incest', 'isis', 'israel',
           'jewish', 'jews', 'jihad', 'kike', 'kill', 'kkk', 'kys', 'loli', 'master race', 'murder', 'nationalist',
           'nazi', 'nazis', 'nigga', 'nigger', 'paedo', 'paki', 'palestin', 'pedo', 'racist', 'rape', 'raping',
           'rapist', 'retard', 'school shoot', 'self harm', 'shoot', 'stab', 'slut', 'spic', 'suicide', 'swastika',
           'terroris', 'torture', 'tranny', 'trump', 'white power', 'you die', 'testingregex123', 'toddl',
           'online conversation', 'online discussion']
# Keyword list from Automod

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

    # sql_config = ConfigParser()
    # bot_config.read('sql_conf.ini')

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
        for log_thing in sr.mod.log(limit=5):  # bot.subreddit("mod").mod.log(limit=20):
            record = is_mod_action_thing_in_database(log_thing)
            time.sleep(0.2)

            if record:
                print(f"{log_thing.id} already in db")
            if not record:
                insert_mod_action_thing_into_database(log_thing, prepare_mod_log_messages(log_thing))
                print(f"{log_thing.id} inserted in db")


def is_mod_action_thing_in_database(log_thing):
    # Note that this is using the prefixed reddit id, ie t3_, t1_
    # do not mix it with the unprefixed version which is called id!
    # Filter by the bot username
    record = mod_log_db_Thing.get_or_none(mod_log_db_Thing.id == log_thing.id)

    return record


def prepare_mod_log_messages(log_thing):
    mod_log_messages = {
        "priv_message": None,
        "pub_message": None}

    if "approvecomment" in log_thing.action and log_thing.mod.name == "AutoModerator":
        return mod_log_messages
    if "approvelink" in log_thing.action and log_thing.mod.name == "AutoModerator":
        return mod_log_messages
    if "distinguish" in log_thing.action:
        return mod_log_messages
    if "addremovalreason" in log_thing.action:
        return mod_log_messages
    if "sticky " in log_thing.action or "unsticky" in log_thing.action:
        return mod_log_messages

    if "AutoModerator" in log_thing.mod.name and log_thing.mod.name == "AutoModerator":
        pub_mod_str = "by: **Automoderator**"
    elif "reddit" in log_thing.mod.name:
        pub_mod_str = "by: **Reddit**"
    elif "Anti-Evil Operations" in log_thing.mod.name:
        pub_mod_str = "by: **Anti-Evil Operations**"
    else:
        pub_mod_str = "by: Mod"
    kw = ""
    if "Automod negative keyword" in log_thing.details and log_thing.target_body:
        count = 0
        kw = "Keyword: "
        for i in kw_list:
            test = log_thing.target_body.lower().find(i)
            if test != -1:
                if count == 0:
                    kw = i
                    count = 1
                else:
                    kw = kw + "," + i
    else:
        kw = ""
    if log_thing.target_body:
        log_thing.target_body = (log_thing.target_body[:300] + '..') if len(
            log_thing.target_body) > 300 else log_thing.target_body
        body = f" : \"{log_thing.target_body}\""
    else:
        body = ""

    if log_thing.details:
        reason = log_thing.details
        if log_thing.description:
            reason = reason + f"({log_thing.description})"
    else:
        reason = ""
    if log_thing.target_author:
        author = f"by u/{log_thing.target_author}:"
    else:
        author = ""
    if log_thing.target_permalink:
        permalink = f"https://reddit.com{log_thing.target_permalink}"
    else:
        permalink = ""
    mod_log_messages["priv_message"] = (
        f"{permalink}{body} {author} **{log_thing.action}** by **{getattr(log_thing.mod, 'name', '')}** because of \"{reason}\" ({kw})\n\n")
    mod_log_messages["pub_message"] = (
        f"{permalink}{body} {author} **{log_thing.action}** {pub_mod_str} because of \"{reason}\" ({kw})\n\n")
    return mod_log_messages


def insert_mod_action_thing_into_database(log_thing, mod_log_messages):
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

    record_dict['modlog_private_message'] = mod_log_messages["priv_message"]
    record_dict['modlog_public_message'] = mod_log_messages["pub_message"]

    return mod_log_db_Thing.create(**record_dict)
