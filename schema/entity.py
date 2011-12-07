import random
import string

class Entity(object):
    def __init__(self, name='thingy', desc=None):
        self.id = Entity.create_id()
        self.components = {}
        self.name = name
        self.desc = desc or 'A {0} sits nearby.'.format(name)

    @staticmethod
    def create_id():
        return ''.join(random.choice(string.ascii_letters) for i in xrange(12))

    def __getitem__(self, com_cls):
        try:
            return self.components[com_cls.__name__]
        except KeyError:
            raise KeyError('{0} has no {1} Component'.format(self, com_cls.__name__))

    def __str__(self):
        ent_str = '\'{0}\' (ID {1})\n'.format(self.name, self.id)
        com_str = '\n'.join('    ' + str(com) for com in self.components.itervalues())
        return ent_str + com_str

    def is_now(self, com_cls, *args, **kwargs):
        self.components[com_cls.__name__] = com_cls(self, *args, **kwargs)

    def is_no_longer(self, com_cls):
        del self.components[com_cls.__name__]

    def is_(self, com_cls):
        return com_cls.__name__ in self.components.iterkeys()

    def tick(self):
        for com in self.components.itervalues():
            com.tick()

    def kill(self):
        for com_name in self.components.keys():
            del self.components[com_name]
        Entity._active -= 1
