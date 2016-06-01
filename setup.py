"""Voting bot for Slack."""

from os import path
from setuptools import setup, find_packages


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), 'r', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name="slack-votebot",
    version="0.0.1a3",
    author="Yoan Blanc",
    author_email="yoan@dosimple.ch",
    homepage="https://github.com/HE-Arc/votebot",
    license="https://opensource.org/licenses/BSD-3-Clause",
    description=__doc__,
    long_description=long_description,
    packages=find_packages(exclude=('contrib', 'docs', 'tests')),
    keywords='slack asyncio bot',
    classifiers=(
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Education",
        "License :: Free For Educational Use",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3 :: Only"
    ),
    install_requires=(
        'aiohttp'
    ),
    extras_require={
        'fast': ('cchardet',),
        'docs': ('sphinx',),
        'tests': (
            'asynctest',
            'pydocstyle',
            'pytest>=2.8',
            'pytest-asyncio',
            'pytest-coverage',
            'pytest-isort',
            'pytest-flake8'
        )
    }
)
