import logging
import inspect

from schema.logger import log
from schema.event import Event

HOOK_TYPES = []

class AspectMeta(type):
    def __new__(cls, name, bases, dict_):
        new_class = super(AspectMeta, cls).__new__(cls, name, bases, dict_)
        if name == 'Aspect':
            return new_class

        new_class.HOOKS = {}
        for method_name, method in inspect.getmembers(new_class):
            if hasattr(method, '_action_regex'):
                # XXX: black magic
                setattr(new_class, method_name, staticmethod(method.im_func))
                Aspect.ACTIONS[method._action_regex] = getattr(new_class, method_name)

            for hook_type in HOOK_TYPES:
                hook_type_attr = '_hook_%s' % hook_type
                if hasattr(method, hook_type_attr):
                    for hooked_function in getattr(method, hook_type_attr):
                        new_class.HOOKS.setdefault(hook_type, {})\
                            .setdefault(hooked_function, [])\
                            .append(getattr(new_class, method_name))

        log.info('Registered aspect: %s' % name)
        Aspect.ALL[name] = new_class
        return new_class


class Aspect(object):
    __metaclass__ = AspectMeta
    ALL = {}
    ACTIONS = {}

    @classmethod
    def class_from_name(cls, name):
        return cls.ALL[name]

    def __init__(self):
        self.entity = None

    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, dict_):
        return cls()

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


def make_hook_decorator(hook_type):
    """A function that generates hook decorators."""
    HOOK_TYPES.append(hook_type)
    def new_hook(action):
        def decorator(f):
            setattr(f, '_hook_%s' % hook_type, [action])
            return f
        return decorator
    return new_hook


before = make_hook_decorator('before')
after = make_hook_decorator('after')
