import asyncpraw as praw
import discord
from praw.models import (Submission as praw_Submission, Comment as praw_Comment, Message as praw_Message)
from db_mod import Thing as db_Thing
from db_mod import create_db_tables
import os
import psycopg2
import time
import asyncio

create_db_tables()

intents = discord.Intents.default()

client = discord.Client(intents=intents)

kw_list = ['aryan', 'assassin', 'auschwitz', 'behead', 'black people', 'bomb', 'child porn', 'chink', 'clinton',
           'columbine', 'concentration camp', 'cunt', 'dago', 'death', 'decapitat', 'dies', 'died', 'drown',
           'execution', 'fag', 'fuck off', 'fuck you', 'genocide', 'hitler', 'holocaust', 'incest', 'isis', 'israel',
           'jewish', 'jews', 'jihad', 'kike', 'kill', 'kkk', 'kys', 'loli', 'master race', 'murder', 'nationalist',
           'nazi', 'nigga', 'nigger', 'paedo', 'paki', 'palestin', 'pedo', 'racist', 'rape', 'raping', 'rapist',
           'retard', 'school shoot', 'self harm', 'shoot', 'stab', 'slut', 'spic', 'suicide', 'swastika', 'terroris',
           'torture', 'tranny', 'trump', 'white power', 'you die']
# Keyword list from Automod


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    bot = praw.Reddit('TEST-GPT2BOT', timeout=64)
    prev_time = 0

    while True:
            await sync_modlog_to_discord(bot)

async def sync_modlog_to_discord(bot):

    sr = await bot.subreddit('SubSimGPT2Interactive')
    async for log_thing in sr.mod.log(limit=50): #bot.subreddit("mod").mod.log(limit=20):
        record = await is_log_thing_in_database(log_thing)

        if record:
            print(f"{log_thing.id} already in db")
        if not record:
            await insert_log_thing_into_database(log_thing)
            #SubSim
            channel_priv = client.get_channel(1057101056796004362) #The channels the bot replies in, pub removes the mod name if the action isn't done by Automod
            channel_pub = client.get_channel(1066096486271692872)

            if "approvecomment" in log_thing.action and log_thing.mod.name == "AutoModerator":
                print(f"{log_thing.id} was disregarded due to \"approvecomment\"")
                continue
            if "approvelink" in log_thing.action and log_thing.mod.name == "AutoModerator":
                print(f"{log_thing.id} was disregarded due to \"approvelink\"")
                continue

            if "AutoModerator" in log_thing.mod.name and log_thing.mod.name == "AutoModerator":
                pub_mod_str = "by: **Automoderator**"
            elif "reddit" in log_thing.mod.name:
                pub_mod_str = "by: **Reddit**"
            elif "Anti-Evil Operations" in log_thing.mod.name:
                pub_mod_str = "by: **Anti-Evil Operations**"
            else:
                pub_mod_str = "by: Mod"
            kw = ""
            if log_thing.details == "Automod negative keyword" and log_thing.target_body:
                count = 0
                for i in kw_list:
                    test = log_thing.target_body.lower().find(i)
                    if test != -1:
                        if count == 0:
                            kw = i
                            count = 1
                        else:
                            kw = kw + ","+i
            else:
                kw = ""
            if log_thing.target_body:
                log_thing.target_body = (log_thing.target_body[:300] + '..') if len(log_thing.target_body) > 300 else log_thing.target_body
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
            log_thing_string_priv = (f"{permalink}{body} {author} **{log_thing.action}** by **{getattr(log_thing.mod, 'name', '')}** because of \"{reason}\" ({kw})\n")
            log_thing_string_pub = (f"{permalink}{body} {author} **{log_thing.action}** {pub_mod_str} because of \"{reason}\" ({kw})\n")
            await channel_pub.send(log_thing_string_pub)
            await channel_priv.send(log_thing_string_priv)
    await asyncio.sleep(15)


async def is_log_thing_in_database(log_thing):
    # Note that this is using the prefixed reddit id, ie t3_, t1_
    # do not mix it with the unprefixed version which is called id!
    # Filter by the bot username
    record = db_Thing.get_or_none(db_Thing.id == log_thing.id)

    return record

async def insert_log_thing_into_database(log_thing):
    # Put the mod action into the db, lazily stolen from ssi-bot
    record_dict = {}
    record_dict['id'] = log_thing.id
    record_dict['created_utc'] = log_thing.created_utc
    record_dict['action'] = log_thing.action
    record_dict['details'] = log_thing.details
    record_dict['mod'] = getattr(log_thing.mod, 'name', '')
    record_dict['target_author'] = log_thing.target_author
    if log_thing.target_body is not None:
        record_dict['target_body'] = log_thing.target_body
    record_dict['target_fullname'] = log_thing.target_fullname
    record_dict['target_permalink'] = log_thing.target_permalink

    return db_Thing.create(**record_dict)
    
mod_log_secret = "E"
client.run(mod_log_secret)
#Run the Discord client, config should be moved in a config file

#if __name__ == '__main__':
#    main()
