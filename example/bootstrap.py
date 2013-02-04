#!/usr/bin/env python

import random
import logging

from schema import Entity, Zone, log
from aspects import *

log.setLevel(logging.DEBUG)

def add_pigeon(room, destinations):
    pigeon = Entity(
        'a pigeon',
        'Hard to believe this thing descended from dinosaurs.',
        [
            Positioned(),
            Bird(noise='coo'),
            Pest(),
            Wandering(wanderlust=0.03, destinations=destinations)
        ],
        zone=room.zone,
    )
    room.Positioned.store(pigeon)

if __name__ == '__main__':
    zone = Zone.from_config('default')
    zone.load_aspects()

    log.info('Bootstrapping new entity set.')

    admin = Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        [Positioned(is_container=True), Emotes(), Admin()],
        zone=zone
    )

    street_north = Entity(
        'The High Street - North',
        'The scent of coffee wafts in on the breeze.',
        [Positioned(is_container=True)],
        zone=zone,
    )

    street_northwest = Entity(
        'The High Street - Northwest',
        'The nearby antique store and public library make fitting neighbors.',
        [Positioned(is_container=True)],
        zone=zone,
    )

    street_northeast = Entity(
        'The High Street - Northeast',
        'An upscale shoe store with stone facade stands next to the brick Fire Station building.',
        [Positioned(is_container=True)],
        zone=zone,
    )

    street_south = Entity(
        'The High Street - South',
        'A street lined with shops extends away from you in both directions.',
        [Positioned(is_container=True)],
        id='startroom',
        zone=zone,
    )

    street_southwest = Entity(
        'The High Street - Southwest',
        'The post office, tailor, and Liara\'s Steakhouse (with outdoor seating) are here.',
        [Positioned(is_container=True)],
        zone=zone,
    )

    street_southeast = Entity(
        'The High Street - Southeast',
        'Raucous music and laughter emanates from the tavern to the south.',
        [Positioned(is_container=True)],
        zone=zone,
    )

    street_south.Positioned.store(admin)

    street_north.Positioned.link('east', street_northeast)
    street_north.Positioned.link('south', street_south)
    street_north.Positioned.link('west', street_northwest)
    street_northwest.Positioned.link('east', street_north)
    street_northwest.Positioned.link('south', street_southwest)
    street_northeast.Positioned.link('west', street_north)
    street_northeast.Positioned.link('south', street_southeast)

    street_south.Positioned.link('north', street_north)
    street_south.Positioned.link('east', street_southeast)
    street_south.Positioned.link('west', street_southwest)
    street_southwest.Positioned.link('east', street_south)
    street_southwest.Positioned.link('north', street_northwest)
    street_southeast.Positioned.link('west', street_south)
    street_southeast.Positioned.link('north', street_northeast)

    ### Northwest side

    # Police station

    police_station = Entity(
        'Police Station - Front Desk',
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    police_station.Positioned.link('south', street_northwest, 'northwest')

    police_offices = Entity(
        'Police Station - Offices',
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    police_offices.Positioned.link('south', police_station, 'north')

    police_interview = Entity(
        'Police Station - Interview Room',
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    police_interview.Positioned.link('east', police_offices, 'west')

    police_locker_room = Entity(
        'Police Station - Locker Room',
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    police_locker_room.Positioned.link('west', police_offices, 'east')

    police_cells = Entity(
        'Police Station - Holding Cells',
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    police_cells.Positioned.link('south', police_offices, 'north')

    police_cell_a = Entity(
        'Cell A',
        '...',
        [Positioned(is_container=True, is_enterable=True)],
        zone=zone,
    )
    police_cell_b = Entity(
        'Cell B',
        '...',
        [Positioned(is_container=True, is_enterable=True)],
        zone=zone,
    )
    police_cell_c = Entity(
        'Cell C',
        '...',
        [Positioned(is_container=True, is_enterable=True)],
        zone=zone,
    )
    police_cell_a.Positioned.link('out', '..')
    police_cell_b.Positioned.link('out', '..')
    police_cell_c.Positioned.link('out', '..')
    police_cells.Positioned.store(police_cell_a)
    police_cells.Positioned.store(police_cell_b)
    police_cells.Positioned.store(police_cell_c)

    # Antique store

    antique_store = Entity(
        "Ye O' Antique Shoppe",
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    antique_store.Positioned.link('south', street_north, 'north')

    # Library

    library = Entity(
        'Public Library',
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    library.Positioned.link('south', street_north, 'northeast')

    ### North side

    # Cafe

    cafe = Entity(
        "Baboman's Cafe",
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    cafe.Positioned.link('south', street_north, 'northwest')

    # Museum

    museum = Entity(
        'The Museum - Rotunda',
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    museum.Positioned.link('south', street_north, 'north')

    # Gift shop

    gift_shop = Entity(
        'The Museum - Gift Shop',
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    gift_shop.Positioned.link('south', street_north, 'northeast')

    ### Northeast side

    ### Southwest side

    # Restaurant

    steakhouse = Entity(
        "Liara's Steakhouse",
        '...',
        [Positioned(is_container=True)],
        zone=zone,
    )
    steakhouse.Positioned.link('north', street_southwest, 'southwest')

    # Tailor

    # Post office

    ### South side

    # Park

    park = Entity(
        'High Street Park',
        'A wide, grassy area.',
        [Positioned(is_container=True)],
        zone=zone,
    )
    park.Positioned.link('north', street_south, 'south')

    ### Southeast side

    # Tavern

    ### Assorted NPCs

    pigeon_destinations = [e.id for e in [
        street_north, street_northwest, street_northeast,
        street_south, street_southwest, street_southeast,
        gift_shop,
    ]]

    # TODO: gift shop manager should scowl at and shoo pigeons

    add_pigeon(street_north, pigeon_destinations)
    add_pigeon(street_northwest, pigeon_destinations)
    add_pigeon(street_southeast, pigeon_destinations)

    zone.save_snapshot()

    log.info('Player ID: %s' % admin.id)
