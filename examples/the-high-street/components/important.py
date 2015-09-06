from figment import Component, before, after
from components import Position

class Important(Component):
    """An item that can't be dropped or taken."""

    @before(Position.drop)
    def prevent_drop(self, event):
        if self.entity == event.target:
            event.actor.tell("You shouldn't get rid of this; it's very important.")
            event.data['prevented'] = True

    @before(Position.put_in)
    def prevent_put_in(self, event):
        if self.entity == event.target:
            event.actor.tell("You shouldn't get rid of this; it's very important.")
            event.data['prevented'] = True

    @before(Position.get)
    def prevent_get(self, event):
        if self.entity == event.target:
            event.actor.tell('{0.Name} resists your attempt to grab it.'.format(self.entity))
            event.data['prevented'] = True

    @before(Position.get_from)
    def prevent_get_from(self, event):
        if self.entity == event.target:
            event.actor.tell('{0.Name} resists your attempt to grab it.'.format(self.entity))
            event.data['prevented'] = True
