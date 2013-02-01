from schema import Aspect, before, after
from aspects import Positioned

class Important(Aspect):
    """An item that can't be dropped or taken."""

    @before(Positioned.drop)
    def prevent_drop(self, event):
        if self.entity == event.target:
            event.actor.tell("You shouldn't get rid of this; it's very important.")
            event.prevent_default()

    @before(Positioned.put_in)
    def prevent_put_in(self, event):
        if self.entity == event.target:
            event.actor.tell("You shouldn't get rid of this; it's very important.")
            event.prevent_default()

    @before(Positioned.get)
    def prevent_get(self, event):
        if self.entity == event.target:
            event.actor.tell('{0.Name} resists your attempt to grab it.'.format(self.entity))
            event.prevent_default()

    @before(Positioned.get_from)
    def prevent_get_from(self, event):
        if self.entity == event.target:
            event.actor.tell('{0.Name} resists your attempt to grab it.'.format(self.entity))
            event.prevent_default()
