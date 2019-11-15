import inspect

from theworldfoundry.components import (
    Named,
    Spatial,
    Container,
    Exit,
    Exitable,
    Emotive,
    Meta,
    Admin,
)
from theworldfoundry.modes import ActionMode


def room(zone, name, desc):
    return zone.spawn([Named(name, inspect.cleandoc(desc)), Spatial(), Container()])


def make_exit(zone, source, direction, destination):
    exit = zone.spawn([Exit(direction=direction, destination_id=destination.id)])

    if not source.is_(Exitable):
        source.components.add(Exitable())

    source.Exitable.exit_ids.add(exit.id)
    source.Exitable.exits.add(exit)


# The identifiers here are bonkers, but it makes the API much easier to use
def connect(zone, destination, is_, of, returning=None):
    make_exit(zone, of, is_, destination)
    if returning:
        make_exit(zone, destination, returning, of)


def make_player(zone):
    player = zone.spawn(
        [
            Named("Test Player", "A player who is here for testing purposes."),
            Spatial(),
            Container(),
            Emotive(),
            Meta(),
            Admin(),
        ],
        hearing=True,
        mode=ActionMode(),
    )

    return player
