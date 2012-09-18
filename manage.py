#!/usr/bin/env python
from flask.ext.script import Manager, Server
from schema.models import Entity, redis, create_world, create_player
from schema.app import app
import json
import os

manager = Manager(app)
manager.add_command('runserver', Server())

def process_command():
    queue_name, queue_item = redis.blpop(['incoming'])

    entity_id, _, command = queue_item.partition(' ')
    entity = Entity.get(entity_id)

    if not entity:
        return

    print '[%s] <%s> %s' % (entity.id, entity.name, command),
    entity.perform(command)
    print '| ok'


@manager.command
def runschema():
    if os.path.exists('dump.json'):
        print 'Loading entities...'
        with open('dump.json', 'r') as f:
            entity_list = json.loads(f.read())
            for entity_dict in entity_list:
                entity = Entity.from_dict(entity_dict)
                print '  [%s] %s' % (entity.id, entity.name)
    else:
        create_world()
        player = create_player()
        print 'Player ID: %s' % player.id
    print 'Listening.'
    while True:
        process_command()


# @manager.command
# def tick():
#     timestamp = datetime.now().strftime('%M:%S.%f')[:-4]
#     print ' * [%s] Tick.' % timestamp
#     for entity in Entity.all():
#         entity.respond_to('on_tick')

if __name__ == '__main__':
    manager.run()
