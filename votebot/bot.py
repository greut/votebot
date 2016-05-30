"""Slack bot."""

import asyncio
import json
import logging

from aiohttp import ClientSession, MsgType

from .api import call
from .utils import extract


class Bot:
    """Slack bot for voting."""

    def __init__(self, token, channel, timeout):
        self.__token = token
        self.channel = channel
        self.channel_id = None
        self.name = 'votebot'
        self.timeout = timeout
        self.future = asyncio.Future()
        self.queue = asyncio.Queue()
        self.log = logging.getLogger(str(self))

    def __str__(self):
        return '<Bot(#{0})>'.format(self.channel)

    def connect(self):
        asyncio.ensure_future(self.run())
        return self.future

    async def call(self, method, file=None, **kwargs):
        return await call(method, file=file, token=self.__token, **kwargs)

    async def run(self):
        """Run the bot by connecting to the Real-Time Messages API."""
        self.rtm = await self.call('rtm.start')

        if not self.rtm['ok']:
            self.future.set_result(ValueError(self.rtm['error']))

        for c in self.rtm['channels']:
            if c['name'] == self.channel:
                self.channel_id = c['id']
                break

        asyncio.ensure_future(self.consume())
        asyncio.ensure_future(self.listen())

    async def listen(self):
        """Listen to the WebSocket URL."""
        async with ClientSession() as session:
            async with session.ws_connect(self.rtm['url']) as ws:
                self.ws = ws
                async for msg in ws:
                    assert msg.tp == MsgType.text
                    message = json.loads(msg.data)
                    await self.queue.put(message)

    async def consume(self):
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

        response = await self.call('chat.postMessage',
                                   channel=self.channel_id,
                                   text='<!channel>: {1} (<@{0}>)'
                                        .format(message['user'], query),
                                   username=self.name,
                                   icon_emoji=':ballot_box_with_ballot:')
        # End of votes.
        asyncio.ensure_future(self.cast_votes(query,
                                              response,
                                              timeout=self.timeout))
        # Adds reactions to it.
        for emoji in emojis:
            asyncio.ensure_future(self.call('reactions.add',
                                            name=emoji.strip(':'),
                                            channel=response['channel'],
                                            timestamp=response['ts']))

    async def cast_votes(self, query, info, timeout):
        done, pending = await asyncio.wait(
            [self.future, asyncio.sleep(timeout)],
            return_when=asyncio.FIRST_COMPLETED
        )

        if self.future in done:
            return

        response = await self.call('reactions.get',
                                    channel=info['channel'],
                                    timestamp=info['ts'])

        fields = []
        for a in response['message']['reactions']:
            # Ignore: non-initial votes.
            if self.rtm['self']['id'] in a['users']:
                fields.append((a['count']-1, a['name']))
        sorted(fields)

        await self.call('chat.postMessage',
                        channel=self.channel_id,
                        username=self.name,
                        attachments=[{
                            'text': '<!channel>: :bar_chart: {0}'
                                    .format(query),
                            'fields': [{'title': ':{0}: {1}'.format(n, c)}
                                        for c, n in fields]
                        }],
                        icon_emoji=':ballot_box_with_ballot:')
