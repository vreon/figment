from schema import Aspect, before
from . import Positioned
import random

class StickyBlob(Aspect):
    """Has a one-in-five chance of dropping successfully."""
    @before(Positioned.drop)
    def stick(self, event):
        if self.entity == event.target:
            if not random.randint(0, 4):
                event.actor.tell('You try to drop {0.name}, but it sticks to your hand.'.format(self.entity))
                event.prevent_default()
