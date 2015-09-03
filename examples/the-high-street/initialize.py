#!/usr/bin/env python

import random
import logging

from figment import Entity, Zone, log
from components import *

log.setLevel(logging.DEBUG)

if __name__ == '__main__':
    zone = Zone.from_config('default', '.')
    zone.load_components()

    # For convenience
    def room(name, desc):
        return Entity(name, desc, [Position(is_container=True)], zone=zone)

    def add_pigeon(room_, destinations):
        pigeon = Entity(
            'a pigeon',
            'Hard to believe this thing descended from dinosaurs.',
            [
                Position(is_carriable=True),
                Bird(noise='coo'),
                Pest(),
                Wandering(wanderlust=0.03, destinations=destinations)
            ],
            zone=zone,
        )
        room_.Position.store(pigeon)


    log.info('Initializing zone.')

    admin = Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        [Position(is_container=True), Emotes()],
        zone=zone,
        hearing=True,
    )

    ##### Ground level

    ### The High Street

    street_north = room(
        'The High Street - North Side',
        (
            'A street lined with shops extends away from you in both '
            'directions. An antique store and library are on the west side, '
            'fitting neighbors. To the east is an upscale shoe store with '
            'stone facade, and the brick Fire Station. The scent of coffee '
            'wafts in on the breeze.'
        ),
    )

    street_south = Entity(
        'The High Street - South Side',
        (
            'A street lined with shops extends away from you in both '
            'directions. On the west side are the post office, tailor, and '
            'Steakhouse (with outdoor seating). Raucous music and laughter '
            'emanates from the tavern to the east.'
        ),
        [Position(is_container=True)],
        id='startroom',
        zone=zone,
    )

    street_south.Position.store(admin)
    street_north.Position.link('south', street_south, 'north')

    ### North side

    # Police station

    police_station = room(
        'Police Station - Front Desk',
        '...',
    )
    police_station.Position.link('south', street_north, 'northwest')

    police_offices = room(
        'Police Station - Offices',
        '...',
    )
    police_offices.Position.link('south', police_station, 'north')

    police_interview = room(
        'Police Station - Interview Room',
        '...',
    )
    police_interview.Position.link('east', police_offices, 'west')

    police_locker_room = room(
        'Police Station - Locker Room',
        '...',
    )
    police_locker_room.Position.link('west', police_offices, 'east')

    police_cells = room(
        'Police Station - Holding Cells',
        '...',
    )
    police_cells.Position.link('south', police_offices, 'north')

    police_cell_a = Entity(
        'Cell A',
        '...',
        [Position(is_container=True, is_enterable=True)],
        zone=zone,
    )
    police_cell_b = Entity(
        'Cell B',
        '...',
        [Position(is_container=True, is_enterable=True)],
        zone=zone,
    )
    police_cell_c = Entity(
        'Cell C',
        '...',
        [Position(is_container=True, is_enterable=True)],
        zone=zone,
    )
    police_cell_a.Position.link('out', '..')
    police_cell_b.Position.link('out', '..')
    police_cell_c.Position.link('out', '..')
    police_cells.Position.store(police_cell_a)
    police_cells.Position.store(police_cell_b)
    police_cells.Position.store(police_cell_c)

    # Antique store

    antique_store = room(
        "Ye O' Antique Shoppe",
        '...',
    )
    antique_store.Position.link('south', street_north, 'north')

    # Library

    library = room(
        'Public Library',
        '...',
    )
    library.Position.link('south', street_north, 'northeast')

    # Cafe

    cafe = room(
        "Baboman's Cafe",
        '...',
    )
    cafe.Position.link('south', street_north, 'northwest')

    # Museum

    museum = room(
        'The Museum - Rotunda',
        '...',
    )
    museum.Position.link('south', street_north, 'north')

    # Gift shop

    gift_shop = room(
        'The Museum - Gift Shop',
        '...',
    )
    gift_shop.Position.link('south', street_north, 'northeast')

    ### South side

    # Restaurant

    steakhouse_lobby = room(
        "Steakhouse",
        '...',
    )
    steakhouse_lobby.Position.link('north', street_south, 'southwest')

    # Tailor

    # Post office

    # Park

    park = room(
        'High Street Park',
        'A wide, grassy area.',
    )
    park.Position.link('north', street_south, 'south')

    ### South side

    # Tavern

    ##### Tall buildings

    ### South side

    # Apartments

    apt_1f_stairwell = room(
        'The Apartments - Stairwell',
        'A concrete stairwell leading from the ground floor to the second.',
    )
    apt_2f_stairwell = room(
        'The Apartments - Stairwell',
        'A concrete stairwell leading from the second floor to the third.',
    )
    apt_3f_stairwell = room(
        'The Apartments - Stairwell',
        'A concrete stairwell leading from the third floor to the fourth.',
    )
    apt_4f_stairwell = room(
        'The Apartments - Stairwell',
        'A concrete stairwell on the fourth floor. The stairs end at a door to the south.',
    )

    apt_2f = room(
        'The Apartments - Second Floor and Leasing Office',
        '...',
    )

    apt_3f = room(
        'The Apartments - Third Floor',
        '...',
    )

    apt_4f = room(
        'The Apartments - Fourth Floor',
        '...',
    )

    apt_elevator = Entity(
        'The Apartments - Elevator',
        "It's out of order for now.",
        [Position(is_container=True)],
        zone=zone,
    )

    steakhouse_lobby.Position.link('east', apt_1f_stairwell, 'west')
    steakhouse_lobby.Position.link('west', apt_elevator, 'east')
    apt_1f_stairwell.Position.link('up', apt_2f_stairwell, 'down')
    apt_2f_stairwell.Position.link('up', apt_3f_stairwell, 'down')
    apt_3f_stairwell.Position.link('up', apt_4f_stairwell, 'down')
    apt_2f_stairwell.Position.link('south', apt_2f, 'north')
    apt_3f_stairwell.Position.link('south', apt_3f, 'north')
    apt_4f_stairwell.Position.link('south', apt_4f, 'north')

    ### Assorted NPCs

    pigeon_destinations = [e.id for e in [
        street_north, street_south, gift_shop,
    ]]

    gift_shop_manager = Entity(
        'the gift shop manager',
        '...',
        [Position(), Emotes(), ShoosPests(direction='south')],
        zone=zone,
    )
    gift_shop.Position.store(gift_shop_manager)

    add_pigeon(street_north, pigeon_destinations)
    add_pigeon(street_north, pigeon_destinations)
    add_pigeon(street_south, pigeon_destinations)

    box = Entity(
        'a cardboard box',
        '...',
        [Position(is_container=True, is_carriable=True, is_enterable=True)], # TODO: is_open
        zone=zone,
    )

    ball = Entity(
        'a rubber ball',
        '...',
        [Position(is_carriable=True)],
        zone=zone,
    )

    cactus = Entity(
        'a cactus',
        '...',
        [Position(is_carriable=True)],
        zone=zone,
    )
    steakhouse_lobby.Position.store(box)
    box.Position.store(ball)
    box.Position.store(cactus)

    zone.save_snapshot()

    log.info('Player ID: %s' % admin.id)
