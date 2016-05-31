Votebot
=======

The bot for voting on stuffs.

Installation
------------

This bot uses extensively features from Python 3.5.

.. code-block:: shell

    $ python3 -m venv slack
    $ cd slack
    $ . bin/activate
    (slack)$ pip install git+https://github.com/HE-Arc/votebot#egg=votebot


Usage
-----

.. code-block:: shell

    (slack)$ export SLACK_TOKEN=xoxb-123
    (slack)$ export SLACK_CHANNEL=general
    (slack)$ export DEBUG=True
    (slack)$ python -m votebot
