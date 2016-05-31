"""Voting bot for Slack."""

from setuptools import setup, find_packages

setup(
    name="votebot",
    version="0.0.1dev20180530",
    author="Yoan Blanc",
    author_email="yoan@dosimple.ch",
    description=__doc__,
    packages=find_packages(),
    install_requires=(
        'aiohttp',
        'cchardet'
    ),
    extras_require={
        'docs': ('sphinx',),
        'tests': ('asynctest',
                  'pydocstyle',
                  'pytest',
                  'pytest-asyncio',
                  'pytest-coverage',
                  'pytest-isort',
                  'pytest-flake8')
    }
)
