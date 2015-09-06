from figment import Component, before
from components import Position

class Psychic(Component):
    @before(Position.say)
    def prepeat(self, event):
        if self.entity.has_component(Position):
            self.entity.perform(Position.say, message=event.message)
