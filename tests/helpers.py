from schema import Entity, Aspect, Zone, action, before, after


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


class Visible(Aspect):
    @action(r'^l(?:ook)?(?: at)? (?P<target>.+)')
    def look_at(event):
        target = Entity.get(event.target)
        if not target:
            event.actor.tell('No such entity %r.' % target)
            return

        event.trigger('before')
        if not event.prevented:
            event.actor.tell(target.desc)


class Colorful(Aspect):
    """An example aspect that includes state and actions."""

    def __init__(self, color='blue'):
        self.color = color

    def to_dict(self):
        return {'color': self.color}

    @classmethod
    def from_dict(cls, dict_):
        self = cls()
        self.color = dict_['color']
        return self

    @action(r'^color(?: of)? (?P<target>.+)')
    def color_of(event):
        target = Entity.get(event.target)
        if not target:
            event.actor.tell('No such entity %r.' % target)
            return

        event.trigger('before')
        if not event.prevented:
            event.actor.tell('{0.Name} is {0.Colorful.color}.'.format(target))

    @action(r'^paint (?P<target>.+) (?P<color>.+)')
    def paint(event):
        target = Entity.get(event.target)
        if not target:
            event.actor.tell('No such entity %r.' % target)
            return

        event.trigger('before')
        if not event.prevented:
            target.Colorful.color = event.color
            event.actor.tell('{0.Name} is now {0.Colorful.color}.'.format(target))


class BlackHole(Aspect):
    """An example aspect that overrides actions from another."""
    @before(Colorful.paint)
    def absorb_paint(self, event):
        if self.entity.id == event.target:
            event.color = 'black'

    @before(Visible.look_at)
    def prevent_look_at(self, event):
        if self.entity.id == event.target:
            event.actor.tell("You're unable to look directly at {0.name}.".format(self.entity))
            event.prevent_default()
