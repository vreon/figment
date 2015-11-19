#!/usr/bin/env python
import logging
from figment import Zone, log
from theworldfoundry import initialize, make_player

log.setLevel(logging.DEBUG)

if __name__ == '__main__':
    zone = Zone.from_config('default', '.')
    zone.load_modules()

    antechamber = initialize(zone)
    player = make_player(zone)
    antechamber.Container.store(player)

    log.info('Player ID: %s' % player.id)

    zone.save_snapshot()
