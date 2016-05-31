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
    debug = 'DEBUG' in os.environ

    if not token:
        print("Please configure a SLACK_TOKEN.",
              file=sys.stderr)
        return 1

    logging.basicConfig(level=logging.INFO)

    five_minutes = 5 * 60
    bot = Bot(token, channel=channel, timeout=five_minutes)

    loop = asyncio.get_event_loop()

    loop.set_debug(debug)
    loop.run_until_complete(bot.connect())
    loop.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
