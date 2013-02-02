#!/usr/bin/env python

import random
import logging

from schema import Entity, Zone, log
from aspects import *

log.setLevel(logging.DEBUG)

def create_player():
    return Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        [Positioned(is_container=True)]
    )

if __name__ == '__main__':
    zone = Zone('default')
    Entity.purge()

    log.info('Bootstrapping new entity set.')

    room = Entity(
        'A Room',
        'A nondescript room.',
        [Positioned(is_container=True), Dark()]
    )

    outside = Entity(
        'Outside',
        'Outside the room.',
        [Positioned(is_container=True)]
    )

    box = Entity(
        'a box',
        'A cardboard box.',
        [Positioned(is_container=True, is_carriable=True, is_enterable=True)]
    )
    box.Positioned.link('out', '..')

    ball = Entity('a ball', 'a rubber ball', [Positioned(is_carriable=True)])

    player = create_player()
    room.Positioned.store(player)
    room.Positioned.store(box)
    box.Positioned.store(ball)

    room.Positioned.link('north', outside, 'south')

    zone.save_snapshot()

    log.info('Player ID: %s' % player.id)
