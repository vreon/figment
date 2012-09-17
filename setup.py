from setuptools import setup, find_packages

setup(
    name = 'schema',
    version = '0.0.1',
    author = 'Jesse Dubay',
    author_email = 'jesse@thefortytwo.net',
    description = (
        'An interactive, text-based MUD engine based on '
        'an entity-component system.'
    ),
    license = 'MIT',
    keywords = 'game engine mud',
    packages=find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        'console_scripts': [
            'schema = schema.cli:cli',
        ],
    }
)
