from figment import Component, before
from components import Position
import random

class StickyBlob(Component):
    """A difficult-to-drop item."""
    def __init__(self, stickiness=0.5):
        self.stickiness = stickiness

    def to_dict(self):
        return {'stickiness': self.stickiness}

    @before(Position.drop)
    def stick(self, event):
        if self.entity == event.target and random.random() < self.stickiness:
            event.actor.tell('You try to drop {0.name}, but it sticks to your hand.'.format(self.entity))
            event.prevent_default()
