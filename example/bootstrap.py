#!/usr/bin/env python

import random

from schema import Entity, Zone
from aspects import *

def create_player():
    return Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        [Positioned(is_container=True)]
    )

if __name__ == '__main__':
    room = Entity(
        'A Room',
        'A nondescript room.',
        [Positioned(is_container=True)]
    )

    player = create_player()
    room.Positioned.store(player)

    zone = Zone('test', 'config.yaml')
    zone.save_snapshot()
