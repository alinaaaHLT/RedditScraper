from reddit_io import RedditIO
import logging
import time
from db import create_db_tables


def main():
	# Use a breakpoint in the code line below to debug your script.
	NEW_LOG_FORMAT = '%(asctime)s (%(threadName)s) %(levelname)s %(message)s'
	logging.basicConfig(format=NEW_LOG_FORMAT, level=logging.INFO)

	create_db_tables()

	bot_io = RedditIO(bot_username="TEST-GPT2BOT")
	bot_io.start()

	try:
		while True:
			time.sleep(5)
	except KeyboardInterrupt:
		logging.info('Shutdown')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
	main()
