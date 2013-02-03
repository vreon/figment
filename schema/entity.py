import random
import string

from schema import jug
from schema.logger import log

class AmbiguousDescriptor(Exception):
    pass

# def action(pattern):
#     def decorator(f):
#         def wrapper(self, *args):
#             try:
#                 return f(self, *[CommandArgument(i, v) for i, v in enumerate(args)])
#             except AmbiguousDescriptor as ex:
#                 descriptor, targets = ex.args
#                 self.mode = DisambiguateMode(
#                     self, self.mode, targets, f.__name__, args, descriptor.index
#                 )
#         ACTIONS[pattern] = wrapper
#         return wrapper
#     return decorator


class CommandArgument(object):
    """
    An 'intelligent parameter' that knows its position in the player
    command. This is so ambiguities can be resolved later.
    """
    def __init__(self, index, value):
        self.index = index
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return 'CommandArgument(%r, %r)' % (self.index, self.value)


class Entity(object):
    ALL = {}

    def __init__(self, name, desc, aspects=None, id=None):
        self.id = id or Entity.create_id()
        self.name = name
        self.desc = desc
        self.mode = ExploreMode(self)
        self.aspects = {}

        if aspects:
            self.apply_aspects(aspects)

        log.debug('Created entity: [%s] %s' % (self.id, self.name))

        Entity.ALL[self.id] = self

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.id == other.id
        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        return NotImplemented if equal is NotImplemented else not equal

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def get(cls, id):
        return cls.ALL.get(id)

    @staticmethod
    def create_id():
        return ''.join(random.choice(string.ascii_letters) for i in xrange(12))

    @classmethod
    def all(cls):
        return cls.ALL.values()

    @classmethod
    def purge(cls):
        log.info('Purging all entities.')
        ids = cls.ALL.keys()
        for id in ids:
            cls.get(id).destroy()

    @property
    def messages_key(self):
        return 'entity:%s:messages' % self.id

    def to_dict(self):
        mode_dict = self.mode.to_dict()
        mode_dict['name'] = self.mode.__class__.__name__
        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'mode': mode_dict,
            'aspects': dict(
                (a.__class__.__name__, a.to_dict()) for a in self.aspects.values()
            )
        }

    @classmethod
    def from_dict(cls, dict_):
        entity = cls(dict_['name'], dict_['desc'], id=dict_['id'])

        mode_dict = dict_['mode']
        mode_name = mode_dict.pop('name')
        entity.mode = Mode.class_from_name(mode_name).from_dict(entity, mode_dict)

        aspects = []
        for aspect_name, aspect_dict in dict_.get('aspects', {}).items():
            aspect = Aspect.class_from_name(aspect_name).from_dict(aspect_dict)
            aspects.append(aspect)

        entity.apply_aspects(aspects)

        cls.ALL[dict_['id']] = entity

        return entity

    # TODO: self.aspects.add()
    # rename self.aspects to self._aspects
    # TODO: force=True skips dependency check
    def apply_aspects(self, aspects):
        for aspect in aspects:
            setattr(self, aspect.__class__.__name__, aspect)
            aspect.entity = self
            self.aspects[aspect.__class__] = aspect

    # TODO: self.aspects.remove()
    def remove_aspects(self, aspect_classes):
        for aspect_class in aspect_classes:
            getattr(self, aspect_class.__name__).destroy()
            delattr(self, aspect_class.__name__)
            self.aspects.pop(aspect_class, None)

    def has_aspect(self, aspect_class):
        return aspect_class in self.aspects

    def destroy(self):
        self.remove_aspects(self.aspects.keys())
        self.ALL.pop(self.id, None)

    def clone(self):
        clone = Entity(self.name, self.desc)

        # TODO: aspects should have a clone method that returns a dict
        # TODO: that way they can determine whether or not to deep copy

        # TODO: Copy properties
        # TODO: Copy behaviors
        # TODO: Copy exits
        # TODO: Clone (not copy) contents
        # TODO: Add clone to clone.container_id's contents

        return clone

    # Sacrificing Pythonic coding style here for convenience.
    @property
    def Name(self):
        return upper_first(self.name)

    def perform(self, command):
        command = ' '.join(command.strip().split())
        self.mode.perform(command)

    def tell(self, message):
        """Send text to this entity."""
        jug.publish(self.messages_key, message)


from schema.utils import upper_first
from schema.modes import Mode, ExploreMode, DisambiguateMode
from schema.aspect import Aspect
