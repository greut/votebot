import re


def extract(message):
    """Split the message and the emojis to be voted for.

    >>> extract('Hello :+1: :-1:')
    ('Hello', [':+1:', ':-1:'])
    >>> extract('Hello :+1:? :-1:')
    ('Hello :+1:?', [':-1:'])
    >>> extract('<@U1> vs <@U2> :snake: :space_invader:')
    ('<@U1> vs <@U2>', [':snake:', ':space_invader:'])
    """
    match = re.search(r':[:a-zA-Z0-9+\-_, ]+$', message)
    query = message[0:match.span()[0]].strip()
    emojis = re.split('[, ]', match.group(0))
    return query, emojis
