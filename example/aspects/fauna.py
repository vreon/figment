from schema import Aspect
from . import Positioned
import random


class Pest(Aspect):
    pass


class Bird(Aspect):
    def __init__(self, noisiness=0.05, noise='chirp'):
        self.noisiness = noisiness
        self.noise = noise

    def to_dict(self):
        return {'noisiness': self.noisiness, 'noise': self.noise}

    @classmethod
    def from_dict(cls, dict_):
        return cls(noisiness=dict_['noisiness'], noise=dict_['noise'])

    def tick(self):
        if random.random() < self.noisiness:
            second_verb, third_verb = random.choice([
                (self.noise, self.noise + 's'),
                ('hop around', 'hops around'),
                ('flutter', 'flutters'),
                ('preen', 'preens'),
                ('peck at the ground', 'pecks at the ground'),
            ])
            self.entity.tell('You {1}.'.format(self.entity, second_verb))

            if not self.entity.has_aspect(Positioned):
                return

            self.entity.Positioned.emit('{0.Name} {1}.'.format(self.entity, third_verb))
