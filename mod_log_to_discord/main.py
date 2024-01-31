import configparser
import pymysql
import discord
import asyncio

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

discord_config = {
    'discord_token': config['discord']['token'],
    'priv_channel_id': config['discord']['priv_channel_id'],
    'pub_channel_id': config['discord']['pub_channel_id']
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def main():
    while True:
        try:
            conn = pymysql.connect(**mysql_config)
            cursor = conn.cursor()
            query = "SELECT * FROM modlog_db WHERE posted IS NULL " \
                    "AND modlog_private_message IS NOT NULL " \
                    "AND modlog_public_message IS NOT NULL " \
                    "LIMIT 100;"
            cursor.execute(query)
            rows = cursor.fetchall()
            field_names = [i[0] for i in cursor.description]

            messages_index = {
                "pub_index": field_names.index("modlog_public_message"),
                "priv_index": field_names.index("modlog_private_message")
            }

            #await send_to_discord(None)
            for row in rows:
                if await send_to_discord(row, messages_index):
                    posted_status_sql = "UPDATE modlog_db SET posted = '1' WHERE id = %s"
                    cursor.execute(posted_status_sql, row[field_names.index("id")])
                else:
                    continue
            conn.commit()
            print("E")



        except Exception as e:
            print(f"An error occurred: {e}")

        await asyncio.sleep(60)



async def send_to_discord(modlog_messages, messages_index):
    try:
        #Prod Server
        test = discord_config['priv_channel_id']
        channel_priv = client.get_channel(int(discord_config['priv_channel_id']))  # The channels the bot replies in, pub removes the mod name if the action isn't done by Automod/reddit/AEO
        channel_pub = client.get_channel(int(discord_config['pub_channel_id']))
        await channel_pub.send(modlog_messages[messages_index["pub_index"]])
        await channel_priv.send(modlog_messages[messages_index["priv_index"]])

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        return 1

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    while True:
            await main()


def start_discord_bot(usename):
    client.run(discord_config['discord_token'])
