from setuptools import setup, find_packages

setup(
    name = 'figment',
    version = '0.0.1',
    author = 'Jesse Dubay',
    author_email = 'jesse@thefortytwo.net',
    description = 'A framework for creating multiplayer, text-based worlds.',
    license = 'MIT',
    keywords = 'game engine mud',
    packages=find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)",
        "License :: OSI Approved :: MIT License",
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
