from collections import defaultdict

class Entity(object):
    _last_id = 0
    _active = 0

    def __init__(self, name='thingy', desc=None):
        Entity._last_id = self.id = Entity._last_id + 1
        Entity._active += 1
        self.components = {}
        self.name = name
        self.desc = desc or 'A {} sits nearby.'.format(name)

    def __getitem__(self, com_cls):
        try:
            return self.components[com_cls.__name__]
        except KeyError:
            raise KeyError('{} has no {} Component'.format(self, com_cls.__name__))

    def __str__(self):
        ent_str = '\'{}\' (ID {})\n'.format(self.name, self.id)
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
