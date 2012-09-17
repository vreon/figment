import sys
import argparse
from schema.models import Entity

def cli():
    parser = argparse.ArgumentParser(description='Manipulates a Schema world.')
    parser.add_argument('entity_id', type=str, help='ID of the target entity')

    subparsers = parser.add_subparsers(dest='command')

    # parser_listen = subparsers.add_parser('listen', help='connect to entity\'s messages stream')
    parser_perform = subparsers.add_parser('perform', help='perform an action from the entity\'s perspective')
    parser_perform.add_argument('action', type=str, help='the action to perform')

    args = parser.parse_args()
    actor = Entity(args.entity_id)

    if not actor:
        print 'fatal: no entity with ID {0}'.format(args.entity_id)
        sys.exit(1)

    if args.command == 'perform':
        actor.perform(args.action)
    # elif args.command == 'listen':
        # actor.listen()
