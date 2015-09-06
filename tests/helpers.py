import re
from figment import Component, Mode


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
    raise AssertionError('%r not found in %r' % (msg, mems))


#############################################################################
# Components
#############################################################################


class Visible(Component):
    """
    A simplified position component.
    """


class Colorful(Component):
    """A test component that includes state."""

    def __init__(self, color='blue'):
        self.color = color

    def to_dict(self):
        return {'color': self.color}


class BlackHole(Component):
    """A test component that affects how actions behave."""


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
            command = ' '.join(command_or_action.strip().split())
            matches = {}
            for pattern, action in ActionMode.ACTIONS.items():
                match = re.match(pattern, command)
                if match:
                    matches[pattern] = (action, match.groupdict())

            # If multiple patterns match this command, pick the longest one
            if matches:
                matching_patterns = matches.keys()
                matching_patterns.sort(key=len, reverse=True)
                action, kwargs = matches[matching_patterns[0]]

        if not action:
            entity.tell('Unknown command.')
            return

        action(entity, **kwargs)

#############################################################################
# Actions
#############################################################################

@ActionMode.action(r'^l(?:ook)?(?: at)? (?P<selector>.+)')
def look_at(actor, selector):
    target = actor.zone.get(selector)
    if not target:
        actor.tell('No such entity %r.' % selector)
        return

    if target.has_component(BlackHole):
        actor.tell("You're unable to look directly at {0.name}.".format(target))
        return

    actor.tell(target.desc)


@ActionMode.action(r'^color(?: of)? (?P<selector>.+)')
def color_of(actor, selector):
    target = actor.zone.get(selector)
    if not target:
        actor.tell('No such entity %r.' % selector)
        return

    if not target.has_component(Colorful):
        actor.tell("{0.Name} has no particular color.".format(target))
        return

    actor.tell('{0.Name} is {0.Colorful.color}.'.format(target))


@ActionMode.action(r'^paint (?P<selector>.+) (?P<color>.+)')
def paint(actor, selector, color):
    target = actor.zone.get(selector)
    if not target:
        actor.tell('No such entity %r.' % selector)
        return

    if not target.has_component(Colorful):
        actor.tell("{0.Name} cannot be painted.".format(target))
        return

    if target.has_component(BlackHole):
        color = 'black'

    target.Colorful.color = color
    actor.tell('{0.Name} is now {0.Colorful.color}.'.format(target))
