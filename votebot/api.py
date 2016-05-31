"""
The `Slack Web API`_ let you communicate with Slack.

Usage
-----

The following example calls the ``api.test`` method which test whether your
token is valid.

.. code-block:: python

    import os
    import asyncio

    from votebot.api import call


    token = os.environ['SLACK_TOKEN']
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(call('api.test',
                                            token=token))
    print(response)
    loop.close()


File upload
-----------

Using the `files.upload`_ API call requires the content to be sent using
``multipart/form-data`` using ``file``.

.. code-block:: python

    with open('myfile.png') as f:
        await call('files.upload',
                   title='Super picture',
                   filename='myfile.png',
                   file=f)


Or send the raw content via ``content``.

.. _Slack Web API: https://api.slack.com/web/
.. _files.upload: https://api.slack.com/methods/files.upload

"""

import json
import logging
from collections.abc import Mapping

from aiohttp import ClientSession, FormData

from .config import SLACK_DOMAIN

LOG = logging.getLogger(__name__)


async def call(method, file=None, **kwargs):
    r"""
    Perform an API call to Slack.

    :param file: File pointer
    :type file: file
    :param **kwargs: see below

    :Keyword Arguments:
        All the arguments required by the method from the `Slack Web API`_.

    :returns: JSON response.
    :rtype: dict
    """
    # JSON encode any sub-structure...
    for k, w in kwargs.items():
        # list, tuple or dict but not a str.
        if isinstance(w, (Mapping, list, tuple)):
            kwargs[k] = json.dumps(w)

    form = FormData(kwargs)

    # Handle file upload
    if file:
        form.add_field('file', file)

    logging.debug('POST /api/{0} {1}'.format(method, form('utf-8')))

    with ClientSession() as session:
        async with session.post('https://{0}/api/{1}'
                                .format(SLACK_DOMAIN, method),
                                data=form) as response:
            assert 200 == response.status, response
            body = await response.json()
            logging.debug('Response /api/{0} {1} {2}'.format(method,
                                                             response.status,
                                                             body))
            return body
