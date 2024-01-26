import sublog.sublog
import modlog.modlog

import threading
import logging
import time


def main():
    # Use a breakpoint in the code line below to debug your script.
    NEW_LOG_FORMAT = '%(asctime)s (%(threadName)s) %(levelname)s %(message)s'
    logging.basicConfig(format=NEW_LOG_FORMAT, level=logging.INFO)
    username = "TEST-GPT2BOT"
    #sublog.sublog.start_sublog()
    tasks = [sublog.sublog.start_sublog, modlog.modlog.start_modlog]
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
