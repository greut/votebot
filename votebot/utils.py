"""Utilitary functions."""
import re


def extract(message):
    """Split the message and the emojis to be voted for.

    :param message: the message to be parsed.
    :type message: str
    :returns: the question and the emojis.
    :rtype: tuple

    >>> extract('Hello :+1::-1:')
    ('Hello', [':+1:', ':-1:'])

    >>> extract('Hello :+1:? :-1:')
    ('Hello :+1:?', [':-1:'])

    >>> extract('No emoji')
    ('No emoji', [':+1:', ':heart:'])

    .. note:: if no emojis are found after the question, you'll automagically
              get the ``:+1:`` as well as the ``:heart:``.
    """
    # FIXME: ugly hack to preserve skin tone.
    message = re.sub(r'::skin-tone-', '§§skin-tone-', message)
    match = re.search(r':[:a-zA-Z0-9+\-_, §]+$', message)
    if not match:
        return message, [':+1:', ':heart:']

    query = message[0:match.span()[0]].strip()
    emojis = re.split('[, ]',
                      match.group(0)
                           .replace('::', ': :')
                           .replace('§§skin-tone', '::skin-tone'))
    return query, emojis
