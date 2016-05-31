"""Slack bot."""

import asyncio
import json
import logging

from aiohttp import ClientSession, MsgType

from .api import call
from .utils import extract


class Bot:
    """Slack bot for voting."""

    def __init__(self, token, *, channel=None, timeout=None):
        """Initialize the bot with a token."""
        self.__token = token
        self.channel = channel or 'random'
        self.channel_id = None
        self.name = 'votebot'
        self.timeout = timeout or 60
        self.future = asyncio.Future()
        self.queue = asyncio.Queue()
        self.log = logging.getLogger(str(self))
        self.rtm = None

    def __str__(self):
        """String representation."""
        return '<Bot(#{0})>'.format(self.channel)

    def connect(self):
        """
        Launch the bot.

        :returns: a future for when the bot wants to be closed.
        :rtype: :py:class:`asyncio.Future`
        """
        asyncio.ensure_future(self._run())
        return self.future

    async def call(self, method, file=None, **kwargs):
        """Wrap the api.call with the token."""
        return await call(method, file=file, token=self.__token, **kwargs)

    async def _run(self):
        """Run the bot by connecting to the Real-Time Messages API."""
        self.rtm = await self.call('rtm.start')

        if not self.rtm['ok']:
            self.future.set_result(ValueError(self.rtm['error']))

        # Searching both into channels and private channels (groups)
        for c in self.rtm['channels']:
            if c['name'] == self.channel:
                self.channel_id = c['id']
                break

        for g in self.rtm['groups']:
            if g['name'] == self.channel:
                self.channel_id = g['id']
                break

        asyncio.ensure_future(self._consume())
        asyncio.ensure_future(self._listen())

    async def _listen(self):
        """Listen to the WebSocket URL."""
        async with ClientSession() as session:
            async with session.ws_connect(self.rtm['url']) as ws:
                self.ws = ws
                async for msg in ws:
                    assert msg.tp == MsgType.text
                    message = json.loads(msg.data)
                    await self.queue.put(message)

    async def _consume(self):
        """Consume the messages from the queue."""
        while True:
            message = await self.queue.get()
            asyncio.ensure_future(self.on_message(message))

    async def on_message(self, message):
        """Handle a message."""
        self.log.debug("GOT {0}".format(message))

        # 'D' means direct channel.
        if 'user' in message and message['user'] == self.rtm['self']['id']:
            return
        if not message.get('channel', '').startswith('D'):
            return
        if not message.get('type', '') == 'message':
            return

        query, emojis = extract(message['text'])
        question = '<!here> (<@{0}>): {1}'.format(message['user'], query)

        self.log.info('Add new question: {0}'.format(question))
        response = await self.call('chat.postMessage',
                                   channel=self.channel_id,
                                   username=self.name,
                                   text=question,
                                   icon_emoji=':ballot_box_with_ballot:')
        # End of votes.
        asyncio.ensure_future(self.cast_votes(question,
                                              response['ts'],
                                              timeout=self.timeout))
        # Adds reactions to it.
        for emoji in emojis:
            self.log.info('Add reaction to {0}: {1}'
                          .format(response['ts'], emoji))
            asyncio.ensure_future(self.call('reactions.add',
                                            name=emoji.strip(':'),
                                            channel=response['channel'],
                                            timestamp=response['ts']))

    async def cast_votes(self, question, timestamp, timeout):
        """
        End a vote by displaying the results and delete the original message.

        :param question: Initial question.
        :type question: str
        :param timestamp: message identifier
        :type timestamp: str
        :param timeout: how many seconds before closing the votes
        :type int:
        """
        self.log.info('Wait {0}s before closing vote.'.format(timeout))
        done, pending = await asyncio.wait(
            [self.future, asyncio.sleep(timeout)],
            return_when=asyncio.FIRST_COMPLETED
        )

        if self.future in done:
            return

        response = await self.call('reactions.get',
                                   channel=self.channel_id,
                                   timestamp=timestamp)

        fields = []
        for a in response['message']['reactions']:
            # Ignore: non-initial votes.
            if self.rtm['self']['id'] in a['users']:
                fields.append((a['count']-1, a['name'], a['users']))
        sorted(fields)

        await self.call('chat.postMessage',
                        channel=self.channel_id,
                        username=self.name,
                        attachments=[{
                            'text': question,
                            'fields': [{'title': ':{0}: {1}'.format(n, c),
                                        'value': ', '.join(self.usernames(*u))}
                                       for c, n, u in fields]
                        }],
                        icon_emoji=':ballot_box_with_ballot:')

        self.log.info("Deleting {0}".format(question))
        await self.call('chat.delete',
                        channel=self.channel_id,
                        ts=timestamp)

    def usernames(self, *ids):
        r"""
        Convert the user ids into username.

        :param \*ids: see below

        :arguments: a list of user identifiers
        """
        ids = set(ids)
        ids.remove(self.rtm['self']['id'])
        for user in self.rtm['users']:
            if user['id'] in ids:
                ids.remove(user['id'])
                yield user['name']
        for i in ids:
            self.log.error('{0} was not found in the RTM.'.format(i))
            yield '<@{0}>'.format(i)
