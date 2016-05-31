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
    def post(self, *args, **kwargs):
        return MockRequest(*args, **kwargs)


class MockRequest:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return MockResponse(200, *self.args, **self.kwargs)

    async def __aexit__(self, *args):
        pass


class MockResponse:
    def __init__(self, status, *args, **kwargs):
        self.status = status
        self.args = args
        self.kwargs = kwargs

    async def json(self):
        return {'ok': False,
                'error': 'I am a mock',
                'args': self.args,
                'kwargs': self.kwargs}


@pytest.mark.asyncio
async def test_api_simple():
    with patch('votebot.api.ClientSession', new=MockClientSession):
        response = await call('api.test', token='xoxb-123')

    assert not response['ok']
    assert 'I am a mock' == response['error']
    assert ('https://slack.com/api/api.test',) == response['args']

    data = response['kwargs']['data']('utf-8')
    assert b'token=xoxb-123' == data


@pytest.mark.asyncio
async def test_api_subfields():
    with patch('votebot.api.ClientSession', new=MockClientSession):
        response = await call('api.dummy', fields=[1, 2, 3])

    data = response['kwargs']['data']('utf-8')
    assert urlencode({'fields': '[1, 2, 3]'}).encode('utf-8') == data


@pytest.mark.asyncio
async def test_api_file(hello_file):
    with patch('votebot.api.ClientSession', new=MockClientSession):
        with open(hello_file, 'r', encoding='utf-8') as f:
            response = await call('api.file', file=f)

    data = response['kwargs']['data']
    assert data.is_multipart
