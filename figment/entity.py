import random
import string
import collections
import inspect

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
            self.components[component.__class__.__name__] = component

        if self.entity.zone and self.entity.ticking:
            self.entity.zone.ticking_entities.add(self.entity)

    def remove(self, component_names):
        if isinstance(component_names, str) or not isinstance(component_names, collections.Iterable):
            component_names = [component_names]

        for component_name in component_names:
            if inspect.isclass(component_name):
                component_name = component_name.__name__
            getattr(self.entity, component_name).detach()
            delattr(self.entity, component_name)
            self.components.pop(component_name, None)

        if self.entity.zone and self.entity in self.entity.zone.ticking_entities and not self.entity.ticking:
            self.entity.zone.ticking_entities.remove(self.entity)

    def has(self, component_names):
        if isinstance(component_names, str) or not isinstance(component_names, collections.Iterable):
            component_names = [component_names]

        for component_name in component_names:
            if inspect.isclass(component_name):
                component_name = component_name.__name__
            if not component_name in self.components:
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
    def from_dict(cls, dict_, zone):
        entity = cls(
            dict_['name'],
            dict_['desc'],
            id=dict_['id'],
            hearing=dict_['hearing'],
        )

        mode_dict = dict_['mode']
        if mode_dict:
            mode_name = mode_dict.pop('__class__')
            mode = zone.modes[mode_name].from_dict(mode_dict)
        else:
            mode = None

        entity.mode = mode
        entity.zone = zone

        components = []
        for component_name, component_dict in dict_.get('components', {}).items():
            component = zone.components[component_name].from_dict(component_dict)
            components.append(component)

        entity.components.add(components)

        return entity

    def is_(self, *args, **kwargs):
        return self.components.has(*args, **kwargs)

    def destroy(self):
        self.components.purge()
        self.zone = None

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
from figment.component import Component
