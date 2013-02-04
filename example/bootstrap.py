#!/usr/bin/env python

import random
import logging

from schema import Entity, Zone, log
from aspects import *

log.setLevel(logging.DEBUG)

def create_player(zone):
    return Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        [Positioned(is_container=True), Emotes(), Admin()],
        zone=zone
    )

if __name__ == '__main__':
    zone = Zone.from_config('default')
    zone.load_aspects()

    log.info('Bootstrapping new entity set.')

    room = Entity(
        'A Room',
        'A nondescript room.',
        [Positioned(is_container=True), Dark()],
        id='startroom',
        zone=zone
    )

    outside = Entity(
        'Outside',
        'Outside the room.',
        [Positioned(is_container=True)],
        zone=zone
    )

    box = Entity(
        'a box',
        'A cardboard box.',
        [Positioned(is_container=True, is_carriable=True, is_enterable=True)],
        zone=zone
    )
    box.Positioned.link('out', '..')

    parrot = Entity(
        'a psychic parrot',
        'A neon purple bird. It scans your mind as you examine it.',
        [Positioned(is_carriable=True), Psychic(), Bird()],
        zone=zone
    )

    blob = Entity('a sticky blob', "It's sticky.", [Positioned(is_carriable=True), StickyBlob()], zone=zone)

    ball = Entity('a ball', 'a rubber ball', [Positioned(is_carriable=True)], zone=zone)

    player = create_player(zone)
    room.Positioned.store(player)
    room.Positioned.store(box)
    room.Positioned.store(parrot)
    box.Positioned.store(ball)
    box.Positioned.store(blob)

    room.Positioned.link('north', outside, 'south')

    zone.save_snapshot()

    log.info('Player ID: %s' % player.id)
