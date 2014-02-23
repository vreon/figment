from __future__ import print_function
import argparse
import readline
import logging
import os
import shutil
from functools import wraps

from figment.zone import Zone
from figment.logger import log


def keyboard_interactive(f):
    """Gracefully handle Ctrl+C and Ctrl+D events."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except (EOFError, KeyboardInterrupt):
            print()
    return wrapper


def new(args):
    skel_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        os.path.pardir,
        'skel'
    )
    shutil.copytree(skel_path, args.name)


def command(args):
    zone = Zone.from_config(args.zone, args.world)
    zone.enqueue_command(args.entity_id, args.command)


@keyboard_interactive
def prompt(args):
    zone = Zone.from_config(args.zone, args.world)
    command = raw_input('> ')
    while command and not command == 'quit':
        zone.enqueue_command(args.entity_id, command)
        command = raw_input('> ')


@keyboard_interactive
def listen(args):
    zone = Zone.from_config(args.zone, args.world)
    for message in zone.listen(args.entity_id):
        print(message)


@keyboard_interactive
def run(args):
    if args.verbose or args.debug:
        log.setLevel(logging.DEBUG)

    try:
        zone = Zone.from_config(args.zone, args.world)

        if args.ticker:
            zone.start_ticker()
        else:
            zone.load_components()
            zone.load_snapshot()
            zone.start()
    except Exception as e:
        if args.debug:
            import pdb
            import sys
            import traceback
            log.critical(traceback.format_exc())
            pdb.post_mortem(sys.exc_info()[2])
        else:
            raise


def cli():
    parser = argparse.ArgumentParser(description='Manipulates a Figment world.')

    parser.add_argument(
        '-z', '--zone', type=str, default='default',
        help='name of the target zone'
    )
    parser.add_argument(
        '-w', '--world', type=str, default='.',
        help='path to the world'
    )

    subparsers = parser.add_subparsers(dest='command')

    # New parser

    parser_new = subparsers.add_parser(
        'new', help='create a new world'
    )
    parser_new.add_argument(
        'name', type=str, help='world name (must be a valid directory name)'
    )
    parser_new.set_defaults(func=new)

    # Listen parser

    parser_listen = subparsers.add_parser(
        'listen', help='connect to an entity\'s message stream'
    )
    parser_listen.add_argument(
        'entity_id', type=str, help='ID of the target entity'
    )
    parser_listen.set_defaults(func=listen)

    # Command parser

    parser_command = subparsers.add_parser(
        'command', help='run a command from the entity\'s perspective'
    )
    parser_command.add_argument(
        'entity_id', type=str, help='ID of the target entity'
    )
    parser_command.add_argument(
        'command', type=str, help='the command to perform'
    )
    parser_command.set_defaults(func=command)

    # Prompt parser

    parser_prompt = subparsers.add_parser(
        'prompt', help='start an interactive prompt for performing commands'
    )
    parser_prompt.add_argument(
        'entity_id', type=str, help='ID of the target entity'
    )
    parser_prompt.set_defaults(func=prompt)

    # Run parser

    parser_run = subparsers.add_parser('run', help='run a Figment zone server')
    parser_run.add_argument(
        '-v', '--verbose', action='store_true',
        help='show verbose output'
    )
    parser_run.add_argument(
        '-d', '--debug', action='store_true',
        help='run pdb if Figment crashes'
    )
    parser_run.add_argument(
        '-t', '--ticker', action='store_true',
        help='run as a tick event generator'
    )
    parser_run.set_defaults(func=run)

    args = parser.parse_args()
    args.func(args)
