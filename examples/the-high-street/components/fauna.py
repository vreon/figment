import random
from figment import Component
from components import position, emotes


class Pest(Component):
    pass


class ShoosPests(Component):
    def __init__(self, direction, awareness=0.2):
        self.awareness = awareness
        self.direction = direction

    def to_dict(self):
        return {'awareness': self.awareness, 'direction': self.direction}

    def tick(self):
        if random.random() >= self.awareness:
            return

        if not self.entity.has_component([position.Position, emotes.Emotes]):
            return

        room = self.entity.Position.container
        pests = set(e for e in room.Position.contents() if e.has_component(Pest))

        if not pests:
            return
        elif len(pests) == 1:
            self.entity.perform(emotes.scowl, selector=list(pests)[0].id)
        else:
            self.entity.perform(emotes.scowl)

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

        self.entity.perform(position.say, message=message)
        self.entity.Position.emit('{0.Name} {1}.'.format(self.entity, action))

        for pest in pests:
            pest.perform(position.walk, direction=self.direction)


class Bird(Component):
    def __init__(self, noisiness=0.05, noise='chirp'):
        self.noisiness = noisiness
        self.noise = noise

    def to_dict(self):
        return {
            'noisiness': self.noisiness,
            'noise': self.noise,
        }

    def tick(self):
        if random.random() >= self.noisiness:
            return

        second_verb, third_verb = random.choice([
            (self.noise, self.noise + 's'),
            ('hop around', 'hops around'),
            ('flutter', 'flutters'),
            ('preen', 'preens'),
            ('peck at the ground', 'pecks at the ground'),
        ])
        self.entity.tell('You {1}.'.format(self.entity, second_verb))

        if not self.entity.has_component(position.Position):
            return

        self.entity.Position.emit('{0.Name} {1}.'.format(self.entity, third_verb))
