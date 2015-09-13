from figment import Component
from components import spatial
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
        if random.random() >= self.wanderlust:
            return

        if not self.entity.is_(spatial.Spatial):
            return

        room = self.entity.Spatial.container

        valid_exits = set()
        for direction, entity in room.Container.exits().items():
            if entity.id in self.destinations:
                valid_exits.add(direction)

        if not valid_exits:
            return

        direction = random.choice(list(valid_exits))
        self.entity.perform(spatial.walk, direction=direction)
