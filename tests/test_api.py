import asyncio

from urllib.parse import urlencode

import pytest

from asynctest import patch
from votebot.api import call


@pytest.fixture(scope='session')
def hello_file(tmpdir_factory):
    fn = tmpdir_factory.mktemp('data').join('hello.txt')
    fn.write('Hello world!\n')
    return str(fn)


class MockClientSession:
    def __enter__(self):
        return MockSession()

    def __exit__(self, *args):
        pass


class MockSession:
    @asyncio.coroutine
    def post(self, *args, **kwargs):
        return MockResponse(200, *args, **kwargs)


class MockResponse:
    def __init__(self, status, *args, **kwargs):
        self.status = status
        self.args = args
        self.kwargs = kwargs

    @asyncio.coroutine
    def __aenter__(self):
        return self

    @asyncio.coroutine
    def __aexit__(self, *args):
        pass

    @asyncio.coroutine
    def release(self):
        pass

    @asyncio.coroutine
    def json(self):
        return {'ok': False,
                'error': 'I am a mock',
                'args': self.args,
                'kwargs': self.kwargs}


@pytest.mark.asyncio
@asyncio.coroutine
def test_api_simple():
    with patch('votebot.api.ClientSession', new=MockClientSession):
        response = yield from call('api.test', token='xoxb-123')

    assert not response['ok']
    assert 'I am a mock' == response['error']
    assert ('https://slack.com/api/api.test',) == response['args']

    data = response['kwargs']['data']('utf-8')
    assert b'token=xoxb-123' == data


@pytest.mark.asyncio
@asyncio.coroutine
def test_api_subfields():
    with patch('votebot.api.ClientSession', new=MockClientSession):
        response = yield from call('api.dummy', fields=[1, 2, 3])

    data = response['kwargs']['data']('utf-8')
    assert urlencode({'fields': '[1, 2, 3]'}).encode('utf-8') == data


@pytest.mark.asyncio
@asyncio.coroutine
def test_api_file(hello_file):
    with patch('votebot.api.ClientSession', new=MockClientSession):
        with open(hello_file, 'r', encoding='utf-8') as f:
            response = yield from call('api.file', file=f)

    data = response['kwargs']['data']
    assert data.is_multipart
