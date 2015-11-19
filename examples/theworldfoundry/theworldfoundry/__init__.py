from figment import log

from theworldfoundry.components import *
from theworldfoundry.modes import *
from theworldfoundry.regions import antechamber, courtyard
from theworldfoundry.utils import link


def make_player(zone):
    player = zone.spawn(
        [
            Named(
                'Test Player',
                'A player who is here for testing purposes.',
            ),
            Spatial(),
            Container(),
            Emotive(),
            Meta(),
            Admin()
        ],
        hearing=True,
        mode=ActionMode()
    )

    return player


def initialize(zone):
    log.info('Initializing zone.')

    refs = {}

    refs['antechamber'] = antechamber.create(zone)
    refs['courtyard'] = courtyard.create(zone)
    link(zone, refs['antechamber']['room'], 'north', refs['courtyard']['south'])

    return refs['antechamber']['room']
