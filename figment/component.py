import inspect

from figment.logger import log

class ComponentMeta(type):
    def __new__(cls, name, bases, dict_):
        new_class = super(ComponentMeta, cls).__new__(cls, name, bases, dict_)
        if name == 'Component':
            return new_class

        for method_name, method in inspect.getmembers(new_class):
            if hasattr(method, '_action_regex'):
                # XXX: black magic
                setattr(new_class, method_name, staticmethod(method.im_func))
                Component.ACTIONS[method._action_regex] = getattr(new_class, method_name)

        return new_class


class Component(object):
    __metaclass__ = ComponentMeta
    ACTIONS = {}

    def __init__(self):
        self.entity = None

    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, dict_):
        return cls(**dict_)

    def attach(self, entity):
        self.entity = entity

    def detach(self):
        self.entity = None

    @property
    def ticking(self):
        return hasattr(self, 'tick')


def action(regex):
    def decorator(f):
        setattr(f, '_action_regex', regex)
        return f
    return decorator
