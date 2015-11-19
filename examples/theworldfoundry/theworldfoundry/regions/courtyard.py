from figment import log

from theworldfoundry.components import *
from theworldfoundry.modes import *
from theworldfoundry.utils import room, link

def create(zone):
    log.info("Creating 'Courtyard'.")

    courtyard_south = room(
        zone,
        'The World Foundry - Courtyard (South Side)',
        """
        TODO: Courtyard description
        """
    )

    statue_south = zone.spawn([
        Named(
            'a large fountain',
            'TODO'
        ),
        Spatial(),
    ])

    courtyard_south.Container.store(statue_south)

    courtyard_north = room(
        zone,
        'The World Foundry - Courtyard (North Side)',
        """
        TODO: Courtyard description
        """
    )

    statue_north = zone.spawn([
        Named(
            'a large fountain',
            'TODO'
        ),
        Spatial(),
    ])

    courtyard_north.Container.store(statue_north)

    link(zone, courtyard_south, 'north', courtyard_north, 'south')

    return {
        'south': courtyard_south,
        'north': courtyard_north,
    }
