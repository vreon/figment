# -*- coding: utf-8 -*-
"""
Figment
~~~~~~~

Figment is a framework for creating multiplayer, text-based worlds. It was
originally designed to explore the application of the "entity-component-system"
pattern to the realm of MUDs.

By extending Figment's base classes (particularly ``Component`` and ``Mode``),
you define the vocabulary unique to your world -- then construct your world's
people, places, and things using that vocabulary.

While your available vocabulary of Components and Modes cannot yet be changed
during runtime, they can be dynamically applied to Entities (that's the whole
point, after all!) so you can even do a good chunk of worldbuilding from within
the world itself.
"""
from setuptools import setup

setup(
    name = 'figment',
    packages = ['figment'],
    version = '0.0.1',
    author = 'Jesse Dubay',
    author_email = 'jesse@jessedubay.com',
    description = 'A framework for creating multiplayer, text-based worlds.',
    long_description = __doc__,
    url = 'https://github.com/vreon/figment',
    license = 'MIT',
    keywords = 'game engine mud',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Communications :: Chat',
        'Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)',
        'Topic :: Games/Entertainment',
    ],
    install_requires=[
        'redis==2.10.3',
        'termcolor==1.1.0',
    ],
    extras_require={
        'YAML': 'PyYAML==3.11',
    },
    entry_points={
        'console_scripts': [
            'figment = figment.cli:cli',
        ],
    }
)
