from figment import Aspect, before
from . import Positioned

class Dark(Aspect):
    @before(Positioned.look)
    def see_nothing(self, event):
        if event.actor in self.contents():
            event.actor.tell("It's too dark to see anything here.")
            event.prevent_default()

    # TODO: prevent look_at if self.target is in self.entity
    # TODO: prevent look_in if self.target is self.entity
