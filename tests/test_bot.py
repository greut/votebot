import pytest

from asynctest import patch
from votebot.bot import Bot


@pytest.fixture()
def bot():
    return Bot('xoxb-123', channel='test')


@pytest.mark.asyncio
async def test_bot_api_test(bot):
    """Test that shows how to create a mock for async."""

    def mock():
        async def call(*args, **kwargs):
            return args, kwargs
        return call

    with patch('votebot.bot.call', new_callable=mock):
        args, kwargs = await bot.call('api.test')

    assert ('api.test',) == args
    assert 'xoxb-123' == kwargs['token']


def test_bot_usernames(monkeypatch, bot):
    """Test that the usernames are correct even when missing."""
    monkeypatch.setattr(bot, 'rtm', {
        'self': {'id': 'U0', 'name': 'bot'},
        'users': [
            {'id': 'U0', 'name': 'bot'},
            {'id': 'U1', 'name': 'john'},
            {'id': 'U2', 'name': 'frank'},
        ]
    })

    names = list(bot.usernames('U0', 'U1', 'U2', 'U3'))
    assert 'bot' not in names, "Self shouldn't appear."
    assert 'john' in names
    assert 'frank' in names
    assert '<@U3>' in names, "Unknown users still appear."
