from schema import Aspect
from . import Positioned
import random


class Wandering(Aspect):
    def __init__(self, wanderlust=0.01, destinations=[]):
        self.wanderlust = wanderlust
        self.destinations = destinations

    def to_dict(self):
        return {
            'wanderlust': self.wanderlust,
            'destinations': self.destinations,
        }

    @classmethod
    def from_dict(cls, dict_):
        return cls(wanderlust=dict_['wanderlust'], destinations=dict_['destinations'])

    def tick(self):
        if random.random() < self.wanderlust:
            if not self.entity.has_aspect(Positioned):
                return

            room = self.entity.Positioned.container

            valid_exits = set()
            for direction, entity in room.Positioned.exits().items():
                if entity.id in self.destinations:
                    valid_exits.add(direction)

            if not valid_exits:
                return

            direction = random.choice(list(valid_exits))
            self.entity.perform(Positioned.walk, direction=direction)
