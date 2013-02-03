from schema import Aspect
from . import Positioned
import random


class Bird(Aspect):
    def __init__(self, noisiness=0.05):
        self.noisiness = noisiness

    def to_dict(self):
        return {'noisiness': self.noisiness}

    @classmethod
    def from_dict(cls, dict_):
        return cls(noisiness=dict_['noisiness'])

    def tick(self):
        if random.random() < self.noisiness:
            second_verb, third_verb = random.choice([
                ('hop around', 'hops around'),
                ('squawk', 'squawks'),
                ('preen', 'preens'),
                ('peck at the ground', 'pecks at the ground'),
            ])
            self.entity.tell('You {1}.'.format(self.entity, second_verb))

            if not self.entity.has_aspect(Positioned):
                return

            self.entity.Positioned.emit('{0.Name} {1}.'.format(self.entity, third_verb))
