import pkg_resources


__version__ = pkg_resources.get_distribution(__package__).version


from .api import call  # noqa
from .bot import Bot  # noqa
