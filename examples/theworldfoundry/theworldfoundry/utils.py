import inspect

from theworldfoundry.components import *

def room(zone, name, desc):
    return zone.spawn([
        Named(name, inspect.cleandoc(desc)),
        Spatial(),
        Container()
    ])


def make_exit(zone, source, direction, destination):
    exit = zone.spawn(
        [Exit(direction=direction, destination_id=destination.id)],
    )

    if not source.is_(Exitable):
        source.components.add(Exitable())

    source.Exitable.exit_ids.add(exit.id)
    source.Exitable.exits.add(exit)


def link(zone, source, direction_to, destination, direction_from=None):
    make_exit(zone, source, direction_to, destination)
    if direction_from:
        make_exit(zone, destination, direction_from, source)
