from __future__ import print_function
import argparse
import readline
import logging
from functools import wraps

from schema import redis
from schema.zone import Zone
from schema.logger import log


def keyboard_interactive(f):
    """Gracefully handle Ctrl+C and Ctrl+D events."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except (EOFError, KeyboardInterrupt):
            print()
    return wrapper


def _perform(zone, entity_id, action):
    zone_key = 'zone:%s:incoming' % zone
    redis.rpush(zone_key, ' '.join((entity_id, action)))


def perform(args):
    _perform(args.zone, args.entity_id, args.action)


@keyboard_interactive
def prompt(args):
    action = raw_input('> ')
    while action and not action == 'quit':
        _perform(args.zone, args.entity_id, action)
        action = raw_input('> ')


@keyboard_interactive
def listen(args):
    # TODO: args.timestamps
    pubsub = redis.pubsub()

    channel = 'entity:%s:messages' % args.entity_id
    pubsub.subscribe(channel)

    print("Listening to %s..." % channel)
    for message in pubsub.listen():
        print(message['data'])


@keyboard_interactive
def run(args):
    if args.debug:
        log.setLevel(logging.DEBUG)
    zone = Zone.from_config(args.zone, args.config)

    if args.ticker:
        zone.start_ticker()
    else:
        zone.load_aspects()
        zone.load_snapshot()
        zone.start()


def cli():
    parser = argparse.ArgumentParser(description='Manipulates a Schema world.')

    subparsers = parser.add_subparsers(dest='command')

    # Listen parser

    parser_listen = subparsers.add_parser(
        'listen', help='connect to an entity\'s message stream'
    )
    parser_listen.add_argument(
        '-z', '--zone', type=str, default='default',
        help='name of the target zone'
    )
    parser_listen.add_argument(
        'entity_id', type=str, help='ID of the target entity'
    )
    parser_listen.set_defaults(func=listen)

    # Perform parser

    parser_perform = subparsers.add_parser(
        'perform', help='perform an action from the entity\'s perspective'
    )
    parser_perform.add_argument(
        '-z', '--zone', type=str, default='default',
        help='name of the target zone'
    )
    parser_perform.add_argument(
        'entity_id', type=str, help='ID of the target entity'
    )
    parser_perform.add_argument(
        'action', type=str, help='the action to perform'
    )
    parser_perform.set_defaults(func=perform)

    # Prompt parser

    parser_prompt = subparsers.add_parser(
        'prompt', help='start an interactive prompt for performing actions'
    )
    parser_prompt.add_argument(
        '-z', '--zone', type=str, default='default',
        help='name of the target zone'
    )
    parser_prompt.add_argument(
        'entity_id', type=str, help='ID of the target entity'
    )
    parser_prompt.set_defaults(func=prompt)

    # Run parser

    parser_run = subparsers.add_parser('run', help='run a schema zone server')
    parser_run.add_argument(
        '-z', '--zone', type=str, default='default',
        help='name of the target zone'
    )
    parser_run.add_argument(
        '-c', '--config', type=str, default='config.json',
        help='path to the config file'
    )
    parser_run.add_argument(
        '-d', '--debug', action='store_true',
        help='show debug output'
    )
    parser_run.add_argument(
        '-t', '--ticker', action='store_true',
        help='run as a tick event generator'
    )
    parser_run.set_defaults(func=run)

    args = parser.parse_args()
    args.func(args)
