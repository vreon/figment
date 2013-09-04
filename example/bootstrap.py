#!/usr/bin/env python

import random
import logging

from figment import Entity, Zone, log
from aspects import *

log.setLevel(logging.DEBUG)

if __name__ == '__main__':
    zone = Zone.from_config('default')
    zone.load_aspects()

    # For convenience
    def room(name, desc):
        return Entity(name, desc, [Positioned(is_container=True)], zone=zone)

    def add_pigeon(room_, destinations):
        pigeon = Entity(
            'a pigeon',
            'Hard to believe this thing descended from dinosaurs.',
            [
                Positioned(is_carriable=True),
                Bird(noise='coo'),
                Pest(),
                Wandering(wanderlust=0.03, destinations=destinations)
            ],
            zone=zone,
        )
        room_.Positioned.store(pigeon)


    log.info('Bootstrapping new entity set.')

    admin = Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        [Positioned(is_container=True), Emotes(), Admin()],
        zone=zone
    )

    ##### Ground level

    ### The High Street

    street_north = room(
        'The High Street - North',
        'The scent of coffee wafts in on the breeze.',
    )

    street_northwest = room(
        'The High Street - Northwest',
        'The nearby antique store and public library make fitting neighbors.',
    )

    street_northeast = room(
        'The High Street - Northeast',
        'An upscale shoe store with stone facade stands next to the brick Fire Station building.',
    )

    street_south = Entity(
        'The High Street - South',
        'A street lined with shops extends away from you in both directions.',
        [Positioned(is_container=True)],
        id='startroom',
        zone=zone,
    )

    street_southwest = room(
        'The High Street - Southwest',
        'The post office, tailor, and Liara\'s Steakhouse (with outdoor seating) are here.',
    )

    street_southeast = room(
        'The High Street - Southeast',
        'Raucous music and laughter emanates from the tavern to the south.',
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

    police_station = room(
        'Police Station - Front Desk',
        '...',
    )
    police_station.Positioned.link('south', street_northwest, 'northwest')

    police_offices = room(
        'Police Station - Offices',
        '...',
    )
    police_offices.Positioned.link('south', police_station, 'north')

    police_interview = room(
        'Police Station - Interview Room',
        '...',
    )
    police_interview.Positioned.link('east', police_offices, 'west')

    police_locker_room = room(
        'Police Station - Locker Room',
        '...',
    )
    police_locker_room.Positioned.link('west', police_offices, 'east')

    police_cells = room(
        'Police Station - Holding Cells',
        '...',
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

    antique_store = room(
        "Ye O' Antique Shoppe",
        '...',
    )
    antique_store.Positioned.link('south', street_north, 'north')

    # Library

    library = room(
        'Public Library',
        '...',
    )
    library.Positioned.link('south', street_north, 'northeast')

    ### North side

    # Cafe

    cafe = room(
        "Baboman's Cafe",
        '...',
    )
    cafe.Positioned.link('south', street_north, 'northwest')

    # Museum

    museum = room(
        'The Museum - Rotunda',
        '...',
    )
    museum.Positioned.link('south', street_north, 'north')

    # Gift shop

    gift_shop = room(
        'The Museum - Gift Shop',
        '...',
    )
    gift_shop.Positioned.link('south', street_north, 'northeast')

    ### Northeast side

    ### Southwest side

    # Restaurant

    steakhouse_lobby = room(
        "Liara's Steakhouse",
        '...',
    )
    steakhouse_lobby.Positioned.link('north', street_southwest, 'southwest')

    # Tailor

    # Post office

    ### South side

    # Park

    park = room(
        'High Street Park',
        'A wide, grassy area.',
    )
    park.Positioned.link('north', street_south, 'south')

    ### Southeast side

    # Tavern

    ##### Tall buildings

    ### Southwest side

    # Apartments

    wards_1f_stairwell = room(
        'The Wards - Stairwell',
        'A concrete stairwell leading from the ground floor to the second.',
    )
    wards_2f_stairwell = room(
        'The Wards - Stairwell',
        'A concrete stairwell leading from the second floor to the third.',
    )
    wards_3f_stairwell = room(
        'The Wards - Stairwell',
        'A concrete stairwell leading from the third floor to the fourth.',
    )
    wards_4f_stairwell = room(
        'The Wards - Stairwell',
        'A concrete stairwell on the fourth floor. The stairs end at a door to the south.',
    )

    wards_2f = room(
        'The Wards - Second Floor and Rental Office',
        '...',
    )

    wards_3f = room(
        'The Wards - Third Floor',
        '...',
    )

    wards_4f = room(
        'The Wards - Fourth Floor',
        '...',
    )

    wards_elevator = Entity(
        'The Wards - Elevator',
        "It's out of order for now.",
        [Positioned(is_container=True)],
        zone=zone,
    )

    steakhouse_lobby.Positioned.link('east', wards_1f_stairwell, 'west')
    steakhouse_lobby.Positioned.link('west', wards_elevator, 'east')
    wards_1f_stairwell.Positioned.link('up', wards_2f_stairwell, 'down')
    wards_2f_stairwell.Positioned.link('up', wards_3f_stairwell, 'down')
    wards_3f_stairwell.Positioned.link('up', wards_4f_stairwell, 'down')
    wards_2f_stairwell.Positioned.link('south', wards_2f, 'north')
    wards_3f_stairwell.Positioned.link('south', wards_3f, 'north')
    wards_4f_stairwell.Positioned.link('south', wards_4f, 'north')

    ### Assorted NPCs

    pigeon_destinations = [e.id for e in [
        street_north, street_northwest, street_northeast,
        street_south, street_southwest, street_southeast,
        gift_shop,
    ]]

    gift_shop_manager = Entity(
        'the gift shop manager',
        '...',
        [Positioned(), Emotes(), ShoosPests(direction='south')],
        zone=zone,
    )
    gift_shop.Positioned.store(gift_shop_manager)

    add_pigeon(street_north, pigeon_destinations)
    add_pigeon(street_northwest, pigeon_destinations)
    add_pigeon(street_southeast, pigeon_destinations)

    box = Entity(
        'a cardboard box',
        '...',
        [Positioned(is_container=True, is_carriable=True, is_enterable=True)], # TODO: is_open
        zone=zone,
    )

    ball = Entity(
        'a rubber ball',
        '...',
        [Positioned(is_carriable=True)],
        zone=zone,
    )

    cactus = Entity(
        'a cactus',
        '...',
        [Positioned(is_carriable=True)],
        zone=zone,
    )
    steakhouse_lobby.Positioned.store(box)
    box.Positioned.store(ball)
    box.Positioned.store(cactus)

    zone.save_snapshot()

    log.info('Player ID: %s' % admin.id)
