import pytest

from figment import Zone, Entity

from theworldfoundry import initialize, make_player
from theworldfoundry.components import *
from theworldfoundry.modes import *


@pytest.fixture()
def zone():
    zone = Zone.from_config('default', '')
    zone.load_modules()
    initialize(zone)
    return zone


@pytest.fixture()
def player(zone):
    antechamber = zone.entities[1]  # FIXME
    player = make_player(zone)
    antechamber.Container.store(player)
    return player


class WitnessError(Exception):
    pass


def tell(entity, msg):
    try:
        entity.memory.append(msg)
    except AttributeError:
        entity.memory = [msg]


def saw(entity, msg):
    try:
        mems = entity.memory
    except AttributeError:
        mems = []

    for mem in mems:
        if msg in mem:
            return True

    raise WitnessError('%r not found in %r' % (msg, mems))


def did_not_see(entity, msg):
    try:
        saw(entity, msg)
    except WitnessError:
        return True

    raise WitnessError('%r found in %r' % (msg, entity.memory))


# I really wanted to call this "neuralyze"
def forget(entity):
    entity.memory = []


@pytest.fixture(autouse=True)
def intercept(request):
    old_tell = Entity.tell

    Entity.tell = tell
    Entity.saw = saw
    Entity.did_not_see = did_not_see
    Entity.forget = forget

    def restore():
        Entity.tell = old_tell

    request.addfinalizer(restore)


###############################################################################
# Helper entities


@pytest.fixture()
def ball(zone, player):
    ball = zone.spawn([
        Named('a red ball', 'A small red ball.'),
        Spatial(),
        Carriable(),
    ])
    player.Spatial.container.Container.store(ball)
    return ball


@pytest.fixture()
def green_ball(zone, player):
    green_ball = zone.spawn([
        Named('a green ball', 'A small green ball.'),
        Spatial(),
        Carriable(),
    ])
    player.Spatial.container.Container.store(green_ball)
    return green_ball


@pytest.fixture()
def statue(zone, player):
    statue = zone.spawn([
        Named('a statue', 'An august marble statue.'),
        Spatial(),
    ])
    player.Spatial.container.Container.store(statue)
    return statue


@pytest.fixture()
def box(zone, player):
    box = zone.spawn([
        Named('a cardboard box', "It's been through a few moves."),
        Spatial(),
        Container(),
        Carriable(),
    ])
    player.Spatial.container.Container.store(box)
    return box


@pytest.fixture()
def iron_box(zone, player):
    iron_box = zone.spawn([
        Named('an iron box', "Looks sturdy!"),
        Spatial(),
        Container(),
        Carriable(),
    ])
    player.Spatial.container.Container.store(iron_box)
    return iron_box


@pytest.fixture()
def pouch(zone, player):
    pouch = zone.spawn([
        Named('a pouch', "Leather, I guess?"),
        Spatial(),
        Container(),
        Carriable(),
    ])
    player.Spatial.container.Container.store(pouch)
    return pouch


@pytest.fixture()
def limo(zone, player):
    limo = zone.spawn([
        Named('a fancy limo', "It's electric!"),
        Spatial(),
        Container(),
        Enterable(),
    ])
    player.Spatial.container.Container.store(limo)
    return limo


@pytest.fixture()
def ghost(zone, player):
    ghost = zone.spawn([
        Named('a ghost', "I-i-it's a g-g-ggg-g-g--"),
        Spatial(),
        Invisible(),
    ])
    player.Spatial.container.Container.store(ghost)
    return ghost
