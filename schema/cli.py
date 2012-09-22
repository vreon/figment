from __future__ import print_function
import sys
import argparse
import json
import yaml
import os
from schema.models import Entity, redis, create_world, create_player
from schema.app import app


def fatal(message):
    print('Fatal: %s' % message)
    sys.exit(1)


def _perform(zone, entity_id, action):
    zone_key = 'zone:%s:incoming' % zone
    redis.rpush(zone_key, ' '.join((entity_id, action)))


def perform(args):
    _perform(args.zone, args.entity_id, args.action)


def prompt(args):
    action = raw_input('> ')
    while action and not action == 'quit':
        _perform(args.zone, args.entity_id, action)
        action = raw_input('> ')


def listen(args):
    # TODO: args.timestamps
    pubsub = redis.pubsub()

    channel = 'entity:%s:messages' % args.entity_id
    pubsub.subscribe('juggernaut')

    print("Listening to %s..." % channel)
    for message in pubsub.listen():
        # Why, juggernaut, why
        payload = json.loads(message['data'])
        if channel in payload['channels']:
            print(payload['data'])


def load_config(path):
    path = os.path.expanduser(path)

    try:
        with open(path) as f:
            config = yaml.safe_load(f)
    except EnvironmentError:
        fatal("couldn't read configuration file")
    except yaml.YAMLError as e:
        fatal("error in configuration file:\n%s" % e)

    return config


def run(args):
    config = load_config(args.config)
    print(config)

    if not args.zone in config['zones']:
        fatal("undefined zone '%s'" % args.zone)

    # TODO: per-zone persistence settings

    persistence = config.get('persistence')
    if not persistence:
        fatal('unspecified persistence settings')

    # TODO: alternate persistence modes

    if not persistence['mode'] == 'snapshot':
        fatal("unrecognized persistence mode '%s'" % persistence['mode'])

    try:
        snapshot_path = persistence['file'] % args.zone
    except TypeError:
        snapshot_path = persistence['file']
    snapshot_path = os.path.expanduser(snapshot_path)

    if os.path.exists(snapshot_path):
        print('Loading entities from snapshot.')
        with open(snapshot_path, 'r') as f:
            entity_list = json.loads(f.read())
            for entity_dict in entity_list:
                entity = Entity.from_dict(entity_dict)
                print('  [%s] %s' % (entity.id, entity.name))
    else:
        create_world()
        player = create_player()
        print('Player ID: %s' % player.id)

    print('Listening.')
    while True:
        process_one_command(args.zone)


def process_one_command(zone):
    zone_key = 'zone:%s:incoming' % zone
    queue_name, queue_item = redis.blpop([zone_key])

    entity_id, _, command = queue_item.partition(' ')
    entity = Entity.get(entity_id)

    if not entity:
        return

    print('[%s] <%s> %s' % (entity.id, entity.name, command))
    entity.perform(command)


def serve(args):
    # TODO: This currently relies on Flask + Juggernaut, but juggernaut is
    # abandoned. Switch to something actively maintained.
    app.run(debug=True)


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
        '-c', '--config', type=str, default='config.yaml',
        help='path to the config file'
    )
    parser_run.set_defaults(func=run)

    # Serve parser

    parser_serve = subparsers.add_parser(
        'serve', help='run a web server for websocket clients'
    )
    parser_serve.set_defaults(func=serve)
    # TODO: host, port

    args = parser.parse_args()
    args.func(args)
