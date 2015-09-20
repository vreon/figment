#!/usr/bin/env python

import random
import logging

from figment import Entity, Zone, log
from components import *
from modes import *

log.setLevel(logging.DEBUG)

if __name__ == '__main__':
    zone = Zone.from_config('default', '.')
    zone.load_modules()

    # For convenience
    def room(name, desc):
        return Entity(name, desc, [Spatial(), Container()], zone=zone)

    def add_pigeon(room_, destination_ids):
        pigeon = Entity(
            'a pigeon',
            'Hard to believe this thing descended from dinosaurs.',
            [
                Spatial(),
                Carriable(),
                Bird(noise='coo'),
                Pest(),
                Wandering(wanderlust=0.03, destination_ids=destination_ids)
            ],
            zone=zone,
            mode=ActionMode(),
        )
        room_.Container.store(pigeon)

    def make_exit(source, direction, destination):
        exit = Entity(
            'an exit',
            'A portal from one location to another.',
            [Exit(direction=direction, destination_id=destination.id)],
            zone=zone,
        )

        if not source.is_(Exitable):
            source.components.add(Exitable())

        source.Exitable.exit_ids.add(exit.id)
        source.Exitable.exits.add(exit)

    def link(source, direction_to, destination, direction_from=None):
        make_exit(source, direction_to, destination)
        if direction_from:
            make_exit(destination, direction_from, source)

    log.info('Initializing zone.')

    admin = Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        [Spatial(), Container(), Emotive(), Meta(), Admin()],
        zone=zone,
        hearing=True,
        id='admin',
        mode=ActionMode()
    )

    trinket = Entity(
        'a shiny trinket',
        'A small metallic gizmo of some kind.',
        [Spatial(), Carriable(), Important()],
        zone=zone,
    )
    admin.Container.store(trinket)

    ##### Ground level

    ### The High Street

    street_north = room(
        'The High Street - North Side',
        (
            'A street lined with shops extends away from you in both '
            'directions. The library lies to the west; to the east is an '
            'upscale shoe store with stone facade, and the brick Fire Station. '
            'The scent of coffee wafts in on the breeze.'
        ),
    )

    street_south = Entity(
        'The High Street - South Side',
        (
            'A street lined with shops extends away from you in both '
            'directions. On the west side is the Steakhouse (with outdoor '
            'seating), above which is a large apartment building. To the east '
            'is the cafe, and directly south are the gentle green hills of '
            'High Street Park.'
        ),
        [Spatial(), Container()],
        zone=zone,
    )

    street_south.Container.store(admin)
    link(street_north, 'south', street_south, 'north')

    statue = Entity(
        'a large statue',
        'A statue of the city founder, looking toward the horizon, rests on a large plinth.',
        [Spatial()],
        zone=zone,
    )
    street_south.Container.store(statue)

    ### North side

    # Library

    library = room(
        'Public Library',
        '...',
    )
    link(library, 'southeast', street_north, 'northwest')

    # Museum

    museum = room(
        'The Museum - Rotunda',
        '...',
    )
    link(museum, 'south', street_north, 'north')

    # Gift shop

    gift_shop = room(
        'The Museum - Gift Shop',
        '...',
    )
    link(gift_shop, 'west', museum, 'east')
    link(gift_shop, 'southwest', street_north, 'northeast')

    ### South side

    # Restaurant

    steakhouse_lobby = room(
        "Steakhouse",
        '...',
    )
    link(steakhouse_lobby, 'northeast', street_south, 'southwest')

    # Park

    park = room(
        'High Street Park',
        'A wide, grassy area.',
    )
    link(park, 'north', street_south, 'south')

    # Cafe

    cafe = room(
        "Baboman's Cafe",
        '...',
    )
    link(cafe, 'northwest', street_south, 'southeast')

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
        [Spatial(), Container()],
        zone=zone,
    )

    link(steakhouse_lobby, 'east', apt_1f_stairwell, 'west')
    link(steakhouse_lobby, 'west', apt_elevator, 'east')
    link(apt_1f_stairwell, 'up', apt_2f_stairwell, 'down')
    link(apt_2f_stairwell, 'up', apt_3f_stairwell, 'down')
    link(apt_3f_stairwell, 'up', apt_4f_stairwell, 'down')
    link(apt_2f_stairwell, 'south', apt_2f, 'north')
    link(apt_3f_stairwell, 'south', apt_3f, 'north')
    link(apt_4f_stairwell, 'south', apt_4f, 'north')

    ### Assorted NPCs

    pigeon_destination_ids = [e.id for e in [
        street_north, street_south, gift_shop,
    ]]

    gift_shop_manager = Entity(
        'the gift shop manager',
        '...',
        [Spatial(), Emotive(), ShoosPests(direction='south')],
        zone=zone,
        mode=ActionMode(),
    )
    gift_shop.Container.store(gift_shop_manager)

    add_pigeon(street_north, pigeon_destination_ids)
    add_pigeon(street_north, pigeon_destination_ids)
    add_pigeon(street_south, pigeon_destination_ids)

    box = Entity(
        'a cardboard box',
        '...',
        [Spatial(), Container(), Carriable(), Enterable()],
        zone=zone,
    )

    ball = Entity(
        'a rubber ball',
        '...',
        [Spatial(), Carriable()],
        zone=zone,
    )

    cactus = Entity(
        'a cactus',
        '...',
        [Spatial(), Carriable()],
        zone=zone,
    )
    steakhouse_lobby.Container.store(box)
    box.Container.store(ball)
    box.Container.store(cactus)

    zone.save_snapshot()

    log.info('Player ID: %s' % admin.id)
