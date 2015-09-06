import random
import string
import collections

from figment.logger import log


class ComponentStore(object):
    def __init__(self, entity):
        self.entity = entity
        self.components = {}

    def add(self, components):
        if not isinstance(components, collections.Iterable):
            components = [components]

        for component in components:
            setattr(self.entity, component.__class__.__name__, component)
            component.attach(self.entity)
            self.components[component.__class__] = component

        if self.entity.zone and self.entity.ticking:
            self.entity.zone.ticking_entities.add(self.entity)

    def remove(self, component_classes):
        if not isinstance(component_classes, collections.Iterable):
            component_classes = [component_classes]

        for component_class in component_classes:
            getattr(self.entity, component_class.__name__).detach()
            delattr(self.entity, component_class.__name__)
            self.components.pop(component_class, None)

        if self.entity.zone and self.entity in self.entity.zone.ticking_entities and not self.entity.ticking:
            self.entity.zone.ticking_entities.remove(self.entity)

    def has(self, component_classes):
        if not isinstance(component_classes, collections.Iterable):
            component_classes = [component_classes]

        for component_class in component_classes:
            if not component_class in self.components:
                return False
        return True

    def purge(self):
        self.remove(self.components.keys())

    def __iter__(self):
        return self.components.values().__iter__()


class Entity(object):
    def __init__(self, name, desc, components=None, id=None, zone=None, hearing=False, mode=None):
        self.id = id or Entity.create_id()
        self.name = name
        self.desc = desc
        self.mode = mode
        self.components = ComponentStore(self)
        self._zone = None
        self.zone = zone
        self.hearing = hearing

        if components:
            self.components.add(components)

        log.debug('Created entity: [%s] %s' % (self.id, self.name))

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.id == other.id
        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        return NotImplemented if equal is NotImplemented else not equal

    def __hash__(self):
        return hash(self.id)

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, value):
        if self._zone is not None:
            self._zone.entities.pop(self.id, None)
            if self in self._zone.ticking_entities:
                self._zone.ticking_entities.remove(self)
        self._zone = value
        if self._zone is not None:
            self._zone.entities[self.id] = self
            if self.ticking:
                self._zone.ticking_entities.add(self)

    @property
    def ticking(self):
        return any(c.ticking for c in self.components)

    @staticmethod
    def create_id():
        return ''.join(random.choice(string.ascii_letters) for i in xrange(12))

    @property
    def messages_key(self):
        return self.messages_key_from_id(self.id)

    @classmethod
    def messages_key_from_id(cls, id):
        return 'entity:%s:messages' % id

    @property
    def hints_key(self):
        return self.hints_key_from_id(self.id)

    @classmethod
    def hints_key_from_id(cls, id):
        return 'entity:%s:hints' % id

    def to_dict(self):
        if self.mode:
            mode_dict = self.mode.to_dict()
            mode_dict['__class__'] = self.mode.__class__.__name__
        else:
            mode_dict = None

        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'mode': mode_dict,
            'hearing': self.hearing,
            'components': dict(
                (c.__class__.__name__, c.to_dict()) for c in self.components
            )
        }

    @classmethod
    def from_dict(cls, dict_, zone=None):
        entity = cls(
            dict_['name'],
            dict_['desc'],
            id=dict_['id'],
            hearing=dict_['hearing'],
        )

        mode_dict = dict_['mode']
        if mode_dict:
            mode_name = mode_dict.pop('__class__')
            mode = Mode.class_from_name(mode_name).from_dict(mode_dict)
        else:
            mode = None

        entity.mode = mode
        entity.zone = zone

        components = []
        for component_name, component_dict in dict_.get('components', {}).items():
            component = Component.class_from_name(component_name).from_dict(component_dict)
            components.append(component)

        entity.components.add(components)

        return entity

    def has_component(self, *args, **kwargs):
        return self.components.has(*args, **kwargs)

    def destroy(self):
        self.components.purge()
        self.zone = None

    def clone(self):
        clone = Entity(self.name, self.desc)

        # TODO: components should have a clone method that returns a dict
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

    def perform(self, *args, **kwargs):
        if self.mode:
            self.mode.perform(self, *args, **kwargs)
        else:
            log.warn('Entity [%s] tried to perform %r, but it has no mode' % (
                self.id, (args, kwargs)
            ))

    def tell(self, message):
        """Send text to this entity."""
        if self.hearing:
            self.zone.redis.publish(self.messages_key, message)


from figment.utils import upper_first
from figment.modes import Mode
from figment.component import Component
