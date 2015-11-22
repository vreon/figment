import pytest

from figment import Zone, Entity

from theworldfoundry.components import *
from theworldfoundry.modes import *
from tests.utils import room, connect, make_player

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

    raise WitnessError('%r not found in:\n\n%s' % (msg, '\n'.join(mems)))


def did_not_see(entity, msg):
    try:
        saw(entity, msg)
    except WitnessError:
        return True

    raise WitnessError('%r found in:\n\n%s' % (msg, '\n'.join(entity.memory)))


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
# Fixtures


@pytest.fixture()
def zone():
    zone = Zone.from_config('default', '')
    zone.load_modules()
    return zone


@pytest.fixture()
def antechamber(zone):
    return room(
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


@pytest.fixture()
def courtyard(zone, antechamber):
    courtyard = room(
        zone,
        'The World Foundry - Courtyard (South Side)',
        """
        A wide-open green space in front of the Library, criss-crossed with a
        network of walking paths.
        """
    )
    connect(zone, courtyard, is_='north', of=antechamber, returning='south')
    return courtyard


@pytest.fixture()
def player(zone, antechamber):
    player = make_player(zone)
    antechamber.Container.store(player)
    return player


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
