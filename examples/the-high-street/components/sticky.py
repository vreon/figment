from figment import Component
import random

class Sticky(Component):
    """A difficult-to-drop item."""
    def __init__(self, stickiness=0.5):
        self.stickiness = stickiness

    def to_dict(self):
        return {'stickiness': self.stickiness}

    def roll_for_drop(self):
        return random.random() < self.stickiness
