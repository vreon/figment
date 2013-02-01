from schema import Aspect, before
from . import Positioned

class Dark(Aspect):
    @before(Positioned.look)
    def see_nothing(self, event):
        # TODO: Ensure that event.actor is contained in self.entity
        event.actor.tell("It's too dark to see anything here.")
        event.prevent_default()

    # TODO: prevent look_at if self.target is in self.entity
    # TODO: prevent look_in if self.target is self.entity
