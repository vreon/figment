from __future__ import print_function
import argparse
from functools import wraps
import importlib
import json
import readline
import logging
import os
from time import sleep
import threading
import subprocess
import sys

from figment.zone import Zone
from figment.logger import log

PROMPT = '\033[32;1m> '
RESET = '\033[m'
ERASE_DOWN = '\033[J'

prompt_quit = False


def prompt(args):
    global prompt_quit

    zone = Zone.from_config(args.zone, args.world)

    while True:
        try:
            command = raw_input(PROMPT)
            if not command or command == 'quit':
                raise EOFError()
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write('\n')
            sys.stdout.flush()
            prompt_quit = True
            break

        zone.enqueue_command(args.entity_id, command)

    sys.stdout.write('\033[m')
    sys.stdout.flush()


def listen(args):
    zone = Zone.from_config(args.zone, args.world)
    subscription = zone.subscribe(args.entity_id)
    renderer = zone.renderer_class()

    while True:
        if prompt_quit:
            break

        message = subscription.get_message()
        if not message:
            sleep(0.01)
            continue

        rendered_message = renderer.render(json.loads(message['data']))

        sys.stdout.write(''.join([
            '\r', RESET, ERASE_DOWN, rendered_message, '\n',
            PROMPT, readline.get_line_buffer()
        ]))
        sys.stdout.flush()


def client(args):
    prompt_thread = threading.Thread(target=lambda: prompt(args))
    listen_thread = threading.Thread(target=lambda: listen(args))

    prompt_thread.start()
    listen_thread.start()

    # TODO HACK: I clearly don't grok threaded exception handling :p

    try:
        prompt_thread.join()
    except KeyboardInterrupt:
        pass

    try:
        listen_thread.join()
    except KeyboardInterrupt:
        pass

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
    except (EOFError, KeyboardInterrupt):
        print()
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

    parser.add_argument('-z', '--zone', type=str, default=os.environ.get('FIGMENT_ZONE', 'default'), help='name of the target zone')
    parser.add_argument('-w', '--world', type=str, default=os.environ.get('FIGMENT_WORLD', ''), help='path to the world')

    subparsers = parser.add_subparsers()

    def cmd(name, func, **kwargs):
        p = subparsers.add_parser(name, **kwargs)
        p.set_defaults(func=func)
        p.arg = lambda *a, **k: p.add_argument(*a, **k) and p
        return p

    cmd('prompt', client, help='start an interactive prompt for performing commands')\
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
