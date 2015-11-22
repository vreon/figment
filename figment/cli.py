from __future__ import print_function
import argparse
import readline
import logging
import sys
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
            zone.load_modules()
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

    parser.add_argument('-z', '--zone', type=str, default='default', help='name of the target zone')
    parser.add_argument('-w', '--world', type=str, default='', help='path to the world')

    subparsers = parser.add_subparsers()

    def cmd(name, func, **kwargs):
        p = subparsers.add_parser(name, **kwargs)
        p.set_defaults(func=func)
        p.arg = lambda *a, **k: p.add_argument(*a, **k) and p
        return p

    cmd('listen', listen, help='connect to an entity\'s message stream')\
        .arg('entity_id', type=int, help='ID of the target entity')

    cmd('command', command, help='run a command from the entity\'s perspective')\
        .arg('entity_id', type=int, help='ID of the target entity')\
        .arg('command', type=str, help='the command to perform')

    cmd('prompt', prompt, help='start an interactive prompt for performing commands')\
        .arg('entity_id', type=int, help='ID of the target entity')

    cmd('run', run, help='run a Figment zone server')\
        .arg('-v', '--verbose', action='store_true', help='show verbose output')\
        .arg('-d', '--debug', action='store_true', help='run pdb if Figment crashes')\
        .arg('-t', '--ticker', action='store_true', help='run as a tick event generator')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    args.func(args)
