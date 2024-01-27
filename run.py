import sublog_to_db.sublog_to_db
import mod_log_to_db.mod_log_to_db
import sub_log_to_csv.sub_log_to_csv

import threading
import logging
import time


def main():
    # Use a breakpoint in the code line below to debug your script.
    NEW_LOG_FORMAT = '%(asctime)s (%(threadName)s) %(levelname)s %(message)s'
    logging.basicConfig(format=NEW_LOG_FORMAT, level=logging.INFO)
    username = "TEST-GPT2BOT"
    #sublog_to_db.sublog_to_db.start_sublog()
    tasks = [sublog_to_db.sublog_to_db.start_sublog, mod_log_to_db.mod_log_to_db.start_modlog, sub_log_to_csv.sub_log_to_csv.main]
    #tasks = [sub_log_to_csv.sub_log_to_csv.main]
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
