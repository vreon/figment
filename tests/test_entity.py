import re
from figment import Entity, Zone, Component, Mode
from figment.utils import upper_first


def tell(self, msg):
    try:
        self.memory.append(msg)
    except AttributeError:
        self.memory = [msg]


def saw(self, msg):
    try:
        mems = self.memory
    except AttributeError:
        mems = []
    for mem in mems:
        if msg in mem:
            return True
    raise AssertionError("%r not found in %r" % (msg, mems))


#############################################################################
# Components
#############################################################################


class Visible(Component):
    """
    A simplified position component.
    """


class Named(Component):
    """Holds human-readable identifying info for an entity."""

    def __init__(self, name=None, desc=None):
        self.name = name
        self.desc = desc

    @property
    def Name(self):
        return upper_first(self.name)

    def to_dict(self):
        return {"name": self.name, "desc": self.desc}

    @classmethod
    def from_dict(cls, dict_):
        return cls(name=dict_["name"], desc=dict_["desc"])


class Colorful(Component):
    """A test component that includes state."""

    def __init__(self, color="blue"):
        self.color = color

    def to_dict(self):
        return {"color": self.color}


class BlackHole(Component):
    """A test component that affects how actions behave."""


class Mooing(Component):
    """Moos at everything every tick."""

    ticking = True

    def tick(self):
        for entity in self.entity.zone.all():
            entity.tell("Moo!")


#############################################################################
# Modes
#############################################################################


class EchoMode(Mode):
    def perform(self, entity, command):
        entity.tell(command)


class ActionMode(Mode):
    ACTIONS = {}

    @classmethod
    def action(cls, regex):
        def register(func):
            cls.ACTIONS[regex] = func
            return func

        return register

    def perform(self, entity, command_or_action, **kwargs):
        action = None

        if callable(command_or_action):
            action = command_or_action
        else:
            command = " ".join(command_or_action.strip().split())
            matches = {}
            for pattern, action in ActionMode.ACTIONS.items():
                match = re.match(pattern, command)
                if match:
                    matches[pattern] = (action, match.groupdict())

            # If multiple patterns match this command, pick the longest one
            if matches:
                matching_patterns = list(matches.keys())
                matching_patterns.sort(key=len, reverse=True)
                action, kwargs = matches[matching_patterns[0]]

        if not action:
            entity.tell("Unknown command.")
            return

        action(entity, **kwargs)


#############################################################################
# Actions
#############################################################################


@ActionMode.action(r"^l(?:ook)?(?: at)? (?P<selector>.+)")
def look_at(actor, selector):
    target = actor.zone.get(int(selector))
    if not target:
        actor.tell("No such entity %r." % selector)
        return

    if target.is_(BlackHole):
        actor.tell("You're unable to look directly at {0.Named.name}.".format(target))
        return

    actor.tell(target.Named.desc)


@ActionMode.action(r"^color(?: of)? (?P<selector>.+)")
def color_of(actor, selector):
    target = actor.zone.get(int(selector))
    if not target:
        actor.tell("No such entity %r." % selector)
        return

    if not target.is_(Colorful):
        actor.tell("{0.Named.Name} has no particular color.".format(target))
        return

    actor.tell("{0.Named.Name} is {0.Colorful.color}.".format(target))


@ActionMode.action(r"^paint (?P<selector>.+) (?P<color>.+)")
def paint(actor, selector, color):
    target = actor.zone.get(int(selector))
    if not target:
        actor.tell("No such entity %r." % selector)
        return

    if not target.is_("Colorful"):
        actor.tell("{0.Named.Name} cannot be painted.".format(target))
        return

    if target.is_("BlackHole"):
        color = "black"

    target.Colorful.color = color
    actor.tell("{0.Named.Name} is now {0.Colorful.color}.".format(target))


class TestEntity:
    @classmethod
    def setup_class(cls):
        Entity.tell = tell
        Entity.saw = saw

    def setup(self):
        self.zone = z = Zone()
        self.player = z.spawn(
            [Named("Player", "A player stands here."), Visible()], mode=ActionMode()
        )
        self.ball = z.spawn(
            [Named("a ball", "A round rubber ball."), Visible(), Colorful(color="red")]
        )
        self.bh = z.spawn(
            [
                Named("black hole", "This text should never appear."),
                Visible(),
                Colorful(color="black"),
                BlackHole(),
            ]
        )
        self.cow = z.spawn([Named("a cow", "A wild dairy cow."), Visible(), Mooing()])

    def test_look_at(self):
        self.player.perform("look at %s" % self.ball.id)
        assert self.player.saw("rubber ball")

    def test_color(self):
        self.player.perform("color of %s" % self.ball.id)
        assert self.player.saw("red")

    def test_paint(self):
        self.player.perform("paint %s blue" % self.ball.id)
        assert self.player.saw("blue")

    def test_absorb_paint(self):
        self.player.perform("paint %s blue" % self.bh.id)
        assert self.player.saw("black")

    def test_look_at_override(self):
        self.player.perform("look at %s" % self.bh.id)
        assert self.player.saw("unable to look directly")

    def test_color_of_uncolorful(self):
        self.player.perform("color of %s" % self.cow.id)
        assert self.player.saw("no particular")

    def test_paint_unpaintable(self):
        self.player.perform("paint %s orange" % self.cow.id)
        assert self.player.saw("cannot be painted")

    def test_add_component(self):
        self.cow.components.add(Colorful(color="green"))
        self.player.perform("color of %s" % self.cow.id)
        assert self.player.saw("green")

    def test_remove_component(self):
        self.ball.components.remove(Colorful)
        self.player.perform("color of %s" % self.ball.id)
        assert self.player.saw("no particular")

    def test_perform_with_action_and_event(self):
        self.player.perform(look_at, selector=self.ball.id)
        assert self.player.saw("rubber")

    def test_echo_mode(self):
        self.player.mode = EchoMode()
        self.player.perform("Echooo")
        assert self.player.saw("Echooo")

    def test_tick(self):
        self.zone.perform_tick()
        assert self.player.saw("Moo!")

    def test_find(self):
        assert self.zone.find(Mooing) == set([self.cow])
        assert self.zone.find("Mooing") == set([self.cow])
