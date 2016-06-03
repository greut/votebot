"""Default bot."""
import asyncio
import logging
import os
import sys

from .bot import Bot


def main(argv):
    """Le bot."""
    token = os.environ.get('SLACK_TOKEN')
    channel = os.environ.get('SLACK_CHANNEL')

    if not token or not channel:
        print("Please configure a SLACK_TOKEN and a SLACK_CHANNEL.",
              file=sys.stderr)
        return 1

    if os.environ.get('DEBUG'):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    five_minutes = 5 * 60
    bot = Bot(token, channel=channel, timeout=five_minutes)

    loop = asyncio.get_event_loop()

    loop.run_until_complete(bot.connect())
    loop.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
