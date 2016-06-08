"""Default bot."""
import asyncio
import logging
import os
import sys

from .bot import Bot
from .config import SLACK_CHANNEL, SLACK_TOKEN, VOTE_TIMEOUT


def main(argv):
    """Le bot."""
    if not SLACK_TOKEN:
        print("Please configure a SLACK_TOKEN.",
              file=sys.stderr)
        return 1

    bot = Bot(SLACK_TOKEN, channel=SLACK_CHANNEL, timeout=VOTE_TIMEOUT)

    if os.environ.get('DEBUG'):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("Starting the votebot on #%s, default timeout %d.",
                SLACK_CHANNEL,
                VOTE_TIMEOUT)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.connect())
    loop.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
