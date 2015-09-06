from figment import Component
from components import Position
import random


class Wandering(Component):
    def __init__(self, wanderlust=0.01, destinations=[]):
        self.wanderlust = wanderlust
        self.destinations = destinations

    def to_dict(self):
        return {
            'wanderlust': self.wanderlust,
            'destinations': self.destinations,
        }

    def tick(self):
        if random.random() < self.wanderlust:
            if not self.entity.is_(Position):
                return

            room = self.entity.Position.container

            valid_exits = set()
            for direction, entity in room.Position.exits().items():
                if entity.id in self.destinations:
                    valid_exits.add(direction)

            if not valid_exits:
                return

            direction = random.choice(list(valid_exits))
            self.entity.perform(Position.walk, direction=direction)
