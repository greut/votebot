"""Global configuration and other magic numbers."""

import os


SLACK_DOMAIN = 'slack.com'
"""Domain used by the Slack server."""

SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
"""Authentication token for the bot."""

SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', 'random')
"""Channel or group to post the polls."""

VOTE_TIMEOUT = int(os.environ.get('VOTE_TIMEOUT', 60))
"""Timeout for all the polls."""
