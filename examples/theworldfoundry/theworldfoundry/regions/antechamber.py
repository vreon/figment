from figment import log

from theworldfoundry.components import *
from theworldfoundry.modes import *
from theworldfoundry.utils import room

def create(zone):
    log.info("Creating 'Antechamber'.")

    antechamber = room(
        zone,
        'The World Foundry - Antechamber',
        """
        A small, comfortable room bordered by red velvet drapes, marble
        columns, and many-hued banners of indeterminate origin.

        This is the Antechamber to the World Foundry, a university dedicated to
        the theory and practice of worldbuilding.

        Beyond the pedestal in the center of the room is an arched oaken door,
        which leads out into the Courtyard.
        """
    )

    return {
        'room': antechamber
    }
