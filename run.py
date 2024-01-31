import sublog_to_db.sublog_to_db as sublog_to_db
import mod_log_to_db.mod_log_to_db as mod_log_to_db
import sub_log_to_csv.sub_log_to_csv as sub_log_to_csv
import mod_log_to_discord.main as mod_log_to_discord

import threading
import logging
import time


def main():
    # Use a breakpoint in the code line below to debug your script.
    NEW_LOG_FORMAT = '%(asctime)s (%(threadName)s) %(levelname)s %(message)s'
    logging.basicConfig(format=NEW_LOG_FORMAT, level=logging.INFO)
    username = "TEST-GPT2BOT"
    #sublog_to_db.sublog_to_db.start_sublog()
    tasks = [sublog_to_db.start_sublog, mod_log_to_db.start_modlog, sub_log_to_csv.main, mod_log_to_discord.start_discord_bot]
    #tasks = [mod_log_to_db.mod_log_to_db.start_modlog]
    #tasks = [mod_log_to_discord.start_discord_bot]
    # thread = Thread(target=test)
    # thread.start()
    for task in tasks:
        t = threading.Thread(target=task, args=(username,))
        t.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info('Shutdown')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
