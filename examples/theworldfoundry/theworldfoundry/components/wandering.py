import random

from figment import Component

from theworldfoundry.components import spatial


class Wandering(Component):
    ticking = True

    def __init__(self, wanderlust=0.01, destination_ids=[]):
        self.wanderlust = wanderlust
        self.destination_ids = destination_ids
        self.destinations = []

    def to_dict(self):
        return {"wanderlust": self.wanderlust, "destination_ids": self.destination_ids}

    def attach(self, entity):
        super(Wandering, self).attach(entity)
        self.destinations = [entity.zone.get(id) for id in self.destination_ids]

    def detach(self):
        self.destinations = []
        super(Wandering, self).detach()

    def tick(self):
        if random.random() >= self.wanderlust:
            return

        if not self.entity.is_(spatial.Spatial):
            return

        room = self.entity.Spatial.container

        if not room.is_(spatial.Exitable):
            return

        valid_exits = set()
        for exit in room.Exitable.exits:
            if exit.Exit.destination in self.destinations:
                valid_exits.add(exit)

        if not valid_exits:
            return

        direction = random.choice(list(valid_exits))
        self.entity.perform(spatial.walk, direction=exit.Exit.direction)
