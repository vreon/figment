# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name = 'theworldfoundry',
    packages = ['theworldfoundry'],
    version = '0.0.1',
    author = 'Jesse Dubay',
    author_email = 'jesse@jessedubay.com',
    description = 'An example Figment world.',
    url = 'https://github.com/vreon/figment/blob/master/examples/theworldfoundry',
    license = 'MIT',
    keywords = 'game engine mud',
    install_requires=[
        'figment',
    ]
)
