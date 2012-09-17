#!/usr/bin/env python
import time
import os
from datetime import datetime
from werkzeug._internal import _log
from werkzeug.serving import run_with_reloader
from flask.ext.script import Manager, Server
from juggernaut import Juggernaut
from schema.app import app
from schema.models import Entity, create_world

manager = Manager(app)
manager.add_command('runserver', Server())

@manager.command
def tick():
    timestamp = datetime.now().strftime('%M:%S.%f')[:-4]
    print ' * [%s] Tick.' % timestamp
    for entity in Entity.all():
        entity.respond_to('on_tick')

@manager.command
def runticker():
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print ' * Ticking.'

    run_with_reloader(tick_server)

def tick_server():
    ticks = 0
    while True:
        tick()
        ticks += 1
        time.sleep(2)

@manager.command
def init():
    create_world()

if __name__ == '__main__':
    manager.run()
