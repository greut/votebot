"""Tricky use cases for the extract function."""

from votebot.utils import extract


def test_preserve_users():
    query, emojis = extract('<@U1> vs <@U2> :snake: :space_invader:')
    assert '<@U1> vs <@U2>' == query
    assert [':snake:', ':space_invader:'] == emojis


def test_preserve_skin_tone():
    query, emojis = extract('? :nose::skin-tone-1::nose:')
    assert '?' == query
    assert [':nose::skin-tone-1:', ':nose:'] == emojis
