from math import sqrt

class Component(object):
    def __init__(self, ent):
        self.ent = ent
    def tick(self):
        pass


class Positionable(Component):
    def __init__(self, ent, x, y):
        super(Positionable, self).__init__(ent)
        self.position = x, y

    def distance_from(self, ent):
        if not ent.is_(Positionable):
            return None
        x1, y1 = self.position
        x2, y2 = ent[Positionable].position
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def __str__(self):
        return 'at position {}'.format(str(self.position))


class Massive(Component):
    def __init__(self, ent, mass):
        super(Massive, self).__init__(ent)
        self.mass = mass

    def __str__(self):
        return 'with mass {} kg'.format(self.mass)


class Damageable(Component):
    class DamageType(object):
        PHYSICAL = 'physical'
        FIRE = 'fire'
        WATER = 'water'
        ELECTRICAL = 'electrical'
        ALL = PHYSICAL, FIRE, WATER, ELECTRICAL

    def __init__(self, ent, hp=100, min=None, max=None):
        super(Damageable, self).__init__(ent)
        self.hp = hp
        self.min = min or 0
        self.max = max or hp

        # Seems pretty reasonable
        self.scale = {
            Damageable.DamageType.PHYSICAL  : 1.0,
            Damageable.DamageType.FIRE      : 1.0,
            Damageable.DamageType.WATER     : 0.0,
            Damageable.DamageType.ELECTRICAL: 0.0,
        }

    def damage(self, type, base_damage):
        old_hp = self.hp
        converted_damage = int(base_damage * self.scale[type])
        self.hp = min(self.max, max(self.min, self.hp - converted_damage))

        if self.hp == self.min and self.ent.is_(Container):
            for item in self.ent[Container].contents.values():
                self.ent[Container].remove(item)

        return old_hp - self.hp

    def alive(self):
        return self.hp > self.min

    def __str__(self):
        damageable_str = 'damageable ({}/{}) '.format(self.hp, self.max)
        scale_str = ' '.join('[{}:{:0.2f}]'.format(k[:2], v) for k, v in self.scale.iteritems())
        return damageable_str + scale_str


class Voluminous(Component):
    def __init__(self, ent, volume):
        super(Voluminous, self).__init__(ent)
        self.volume = volume

    def __str__(self):
        return 'occupies {} cm^3'.format(self.volume)


class Container(Component):
    class Result(object):
        ALL = OK, UNSTORABLE, ALREADY_STORED, TOO_HEAVY, TOO_BIG = range(5)

    def __init__(self, ent, max_volume=1000000, max_mass=1000000):
        super(Container, self).__init__(ent)
        self.max_volume = max_volume
        self.max_mass = max_mass
        self.contents = {}

    def _contents_volume(self):
        return sum(ent[Voluminous].volume for ent in self.contents.itervalues())

    def _contents_mass(self):
        return sum(ent[Massive].mass for ent in self.contents.itervalues())

    def store(self, ent):
        if ent.is_(Voluminous) and ent[Voluminous].volume + self._contents_volume() > self.max_volume:
            return Container.Result.TOO_BIG

        if ent.is_(Massive) and ent[Massive].mass + self._contents_mass() > self.max_mass:
            return Container.Result.TOO_HEAVY

        if not ent.is_(Storable):
            return Container.Result.UNSTORABLE

        if ent[Storable].container is not None:
            return Container.Result.ALREADY_STORED

        self.contents[ent.id] = ent
        ent[Storable].container = self.ent

        if ent.is_(Positionable):
            ent.is_no_longer(Positionable)

        if self.ent.is_(Massive):
            self.ent[Massive].mass += ent[Massive].mass

        return Container.Result.OK

    def remove(self, ent):
        if ent.is_(Storable) and ent[Storable].container is not None and \
        ent[Storable].container.id == self.ent.id:
            del self.contents[ent.id]
            ent[Storable].container = None

            if self.ent.is_(Massive):
                self.ent[Massive].mass -= ent[Massive].mass

            if self.ent.is_(Positionable):
                x, y = self.ent[Positionable].position
                ent.is_now(Positionable, x, y)

            return True
        return False

    def __str__(self):
        return 'is container ({} entit{}, {}/{} cm^3, {}/{} kg)'.format(
            len(self.contents),
            'y' if len(self.contents) == 1 else 'ies',
            self._contents_volume(), self.max_volume,
            self._contents_mass(), self.max_mass
        )


class Storable(Component):
    def __init__(self, ent):
        super(Storable, self).__init__(ent)
        self.container = None

    def __str__(self):
        return 'stored in entity #{}'.format(self.container.id) if self.container else 'not stored'


class Flammable(Component):
    def __init__(self, ent):
        super(Flammable, self).__init__(ent)
        self.burning = False

    def tick(self):
        if self.burning and self.ent.is_(Damageable):
            self.ent[Damageable].damage(Damageable.DamageType.FIRE, 5)

    def __str__(self):
        return 'burning' if self.burning else 'flammable'


class Soakable(Component):
    def __init__(self, ent):
        super(Soakable, self).__init__(ent)
        self.soaked = False

    def tick(self):
        if self.soaked and self.ent.is_(Damageable):
            self.ent[Damageable].damage(Damageable.DamageType.WATER, 5)

    def __str__(self):
        return 'soaked' if self.soaked else 'soakable'
