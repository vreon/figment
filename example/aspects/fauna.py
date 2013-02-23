from schema import Aspect
from . import Positioned, Emotes
import random


class Pest(Aspect):
    pass


class ShoosPests(Aspect):
    def __init__(self, direction, awareness=0.2):
        self.awareness = awareness
        self.direction = direction

    def to_dict(self):
        return {'awareness': self.awareness, 'direction': self.direction}

    def tick(self):
        if random.random() < self.awareness:
            if not self.entity.has_aspect(Positioned):
                return

            room = self.entity.Positioned.container
            pests = set(e for e in room.Positioned.contents() if e.has_aspect(Pest))

            if not pests:
                return
            elif len(pests) == 1:
                self.entity.perform(Emotes.scowl, descriptor=list(pests)[0].id)
            else:
                self.entity.perform(Emotes.scowl)

            message = ', '.join([
                random.choice([
                    'Agh! Scram', 'Get outta here', 'Ksss! Shoo', 'Hey! Beat it'
                ]),
                random.choice([
                    'you vermin!', 'you!',
                ])
            ])

            action = random.choice([
                'swings a broom',
                'flails his arms',
                'takes a menacing step toward the door',
                'shouts obscenities',
            ])

            self.entity.perform(Positioned.say, message=message)
            self.entity.Positioned.emit('{0.Name} {1}.'.format(self.entity, action))

            for pest in pests:
                pest.perform(Positioned.walk, direction=self.direction)

class Bird(Aspect):
    def __init__(self, noisiness=0.05, noise='chirp'):
        self.noisiness = noisiness
        self.noise = noise

    def to_dict(self):
        return {'noisiness': self.noisiness, 'noise': self.noise}

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
