"""
Votebot module.

See ``__main__.py`` for more details on how to use it.
"""

import pkg_resources


__version__ = pkg_resources.get_distribution('votebot').version

from .api import call  # noqa
from .bot import Bot  # noqa
from .utils import extract  # noqa
