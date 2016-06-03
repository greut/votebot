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

    @asyncio.coroutine
    def call(self, method, file=None, **kwargs):
        """Wrap the api.call with the token."""
        return (yield from call(method,
                                file=file,
                                token=self.__token,
                                **kwargs))

    @asyncio.coroutine
    def _run(self):
        """Run the bot by connecting to the Real-Time Messages API."""
        self.rtm = yield from self.call('rtm.start')

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

    @asyncio.coroutine
    def _listen(self):
        """Listen to the WebSocket URL."""
        with ClientSession() as session:
            ws = yield from session._ws_connect(self.rtm['url'])
            self.ws = ws
            try:
                while True:
                    msg = yield from ws.receive()
                    if msg.tp == MsgType.close:
                        break

                    assert msg.tp == MsgType.text
                    message = json.loads(msg.data)
                    yield from self.queue.put(message)
            finally:
                yield from ws.close()

    @asyncio.coroutine
    def _consume(self):
        """Consume the messages from the queue."""
        while True:
            message = yield from self.queue.get()
            asyncio.ensure_future(self.on_message(message))

    @asyncio.coroutine
    def on_message(self, message):
        """Handle a message."""
        self.log.debug("GOT %s", message)

        # 'D' means direct channel.
        if 'user' in message and message['user'] == self.rtm['self']['id']:
            return
        if not message.get('channel', '').startswith('D'):
            return
        if not message.get('type', '') == 'message':
            return

        question, emojis = extract(message['text'])

        self.log.info('Add new question: %s', question)
        response = yield from self.call(
            'chat.postMessage',
            channel=self.channel_id,
            username=self.name,
            text="<!here>",
            attachments=[{
                "title": question,
                "fields": [{
                    "title": "By",
                    "value": "".join(self.usernames(message['user'])),
                    "short": True,
                },{
                    "title": "Duration",
                    "value": "{0:.1f}m".format(self.timeout / 60),
                    "short": True,
                }],
            }],
            icon_emoji=':ballot_box_with_ballot:')
        # End of votes.
        asyncio.ensure_future(self.cast_votes(question,
                                              response['ts'],
                                              timeout=self.timeout))
        # Adds reactions to it.
        for emoji in emojis:
            self.log.info('Add reaction to %s: %s',
                          response['ts'], emoji)
            asyncio.ensure_future(self.call('reactions.add',
                                            name=emoji.strip(':'),
                                            channel=response['channel'],
                                            timestamp=response['ts']))

    @asyncio.coroutine
    def cast_votes(self, question, timestamp, timeout):
        """
        End a vote by displaying the results and delete the original message.

        :param question: Initial question.
        :type question: str
        :param timestamp: message identifier
        :type timestamp: str
        :param timeout: how many seconds before closing the votes
        :type int:
        """
        self.log.info('Wait %ds before closing vote.', timeout)
        done, pending = yield from asyncio.wait(
            [self.future, asyncio.sleep(timeout)],
            return_when=asyncio.FIRST_COMPLETED
        )

        if self.future in done:
            return

        response = yield from self.call('reactions.get',
                                        channel=self.channel_id,
                                        timestamp=timestamp)

        fields = []
        for a in response['message']['reactions']:
            # Ignore: non-initial votes.
            if self.rtm['self']['id'] in a['users']:
                fields.append((a['count']-1, a['name'], a['users']))
        sorted(fields)

        attachments = [{
            'text': question,
            'fields': [{'title': ':{0}: {1}'.format(n, c),
                        'value': ', '.join(self.usernames(*u))}
                       for c, n, u in fields]
        }]

        asyncio.ensure_future(self.call('chat.postMessage',
                                        channel=self.channel_id,
                                        username=self.name,
                                        attachments=attachments,
                                        icon_emoji=':ballot_box_with_ballot:'))

        self.log.info("Deleting %s", question)
        asyncio.ensure_future(self.call('chat.delete',
                                        channel=self.channel_id,
                                        ts=timestamp))

    def usernames(self, *ids):
        r"""
        Convert the user ids into username.

        :param \*ids: see below

        :arguments: a list of user identifiers
        """
        ids = set(ids)
        me = self.rtm['self']['id']
        if me in ids:
            ids.remove(me)
        for user in self.rtm['users']:
            if user['id'] in ids:
                ids.remove(user['id'])
                yield user['name']
        for id_ in ids:
            self.log.error('%s was not found in the RTM.', id_)
            yield '<@{0}>'.format(id_)
