from schema import Aspect, before
from .positioned import Positioned
import random

class StickyBlob(Aspect):
    """Has a one-in-five chance of dropping successfully."""
    @before(Positioned.drop)
    def stick(self, event):
        if self.entity == event.target:
            if random.randint(1, 5) != 1:
                event.actor.tell('You try to drop {0.name}, but it sticks to your hand.'.format(self.entity))
                event.prevent_default()
