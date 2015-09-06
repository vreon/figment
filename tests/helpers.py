from figment import Component, action, before


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


class Visible(Component):
    """
    A simplified position component. It doesn't do selector resolution (you
    have to use the entity ID).
    """

    @action(r'^l(?:ook)?(?: at)? (?P<selector>.+)')
    def look_at(event):
        target = event.actor.zone.get(event.selector)
        if not target:
            event.actor.tell('No such entity %r.' % event.selector)
            return

        yield 'before', event.actor.zone.all()
        if event.data.get('prevented'):
            return

        event.actor.tell(target.desc)


class Colorful(Component):
    """A test component that includes state and actions."""

    def __init__(self, color='blue'):
        self.color = color

    def to_dict(self):
        return {'color': self.color}

    @action(r'^color(?: of)? (?P<selector>.+)')
    def color_of(event):
        target = event.actor.zone.get(event.selector)
        if not target:
            event.actor.tell('No such entity %r.' % event.selector)
            return

        if not target.has_component(Colorful):
            event.actor.tell("{0.Name} has no particular color.".format(target))
            return

        yield 'before', event.actor.zone.all()
        if event.data.get('prevented'):
            return

        event.actor.tell('{0.Name} is {0.Colorful.color}.'.format(target))

    @action(r'^paint (?P<selector>.+) (?P<color>.+)')
    def paint(event):
        target = event.actor.zone.get(event.selector)
        if not target:
            event.actor.tell('No such entity %r.' % event.selector)
            return

        if not target.has_component(Colorful):
            event.actor.tell("{0.Name} cannot be painted.".format(target))
            return

        yield 'before', event.actor.zone.all()
        if event.data.get('prevented'):
            return

        target.Colorful.color = event.color
        event.actor.tell('{0.Name} is now {0.Colorful.color}.'.format(target))


class BlackHole(Component):
    """A test component that overrides actions from another."""
    @before(Colorful.paint)
    def absorb_paint(self, event):
        if self.entity.id == event.selector:
            event.color = 'black'

    @before(Visible.look_at)
    def prevent_look_at(self, event):
        if self.entity.id == event.selector:
            event.actor.tell("You're unable to look directly at {0.name}.".format(self.entity))
            event.data['prevented'] = True
