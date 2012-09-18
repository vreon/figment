import sys
import argparse
import json
from schema.models import Entity, redis

def cli():
    parser = argparse.ArgumentParser(description='Manipulates a Schema world.')
    parser.add_argument('entity_id', type=str, help='ID of the target entity')

    subparsers = parser.add_subparsers(dest='command')

    parser_listen = subparsers.add_parser('listen', help='connect to entity\'s messages stream')
    parser_perform = subparsers.add_parser('perform', help='perform an action from the entity\'s perspective')
    parser_perform.add_argument('action', type=str, help='the action to perform')

    args = parser.parse_args()

    if args.command == 'perform':
        redis.rpush('incoming', ' '.join((args.entity_id, args.action)))
    elif args.command == 'listen':
        pubsub = redis.pubsub()

        channel = 'entity:%s:messages' % args.entity_id
        pubsub.subscribe('juggernaut')

        print "Listening to %s..." % channel
        for message in pubsub.listen():
            # Why, juggernaut, why
            payload = json.loads(message['data'])
            if channel in payload['channels']:
                print payload['data']
