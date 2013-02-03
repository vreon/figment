import re
import random
from schema import redis
from schema.aspect import Aspect
from schema.event import Event
from schema.utils import int_or_none

# For Python 3 compatibility
try:
    basestring
except NameError:
    basestring = (str, bytes)

class ModeMeta(type):
    def __new__(cls, name, bases, dict_):
        new_class = super(ModeMeta, cls).__new__(cls, name, bases, dict_)
        if name != 'Mode':
            Mode.ALL[name] = new_class
        return new_class


class Mode(object):
    __metaclass__ = ModeMeta
    ALL = {}

    @classmethod
    def class_from_name(cls, name):
        return cls.ALL[name]

    def __init__(self, entity):
        self.entity = entity

    @classmethod
    def from_dict(cls, entity, dict_):
        return cls(entity)

    def to_dict(self):
        return {}

    def perform(self, command):
        raise NotImplementedError


class ExploreMode(Mode):
    def perform(self, command_or_action, **kwargs):
        event = None
        action = None

        if isinstance(command_or_action, basestring):
            command = ' '.join(command_or_action.strip().split())
            matches = {}
            for pattern, action in Aspect.ACTIONS.items():
                match = re.match(pattern, command)
                if match:
                    matches[pattern] = (action, match.groupdict())

            # If multiple patterns match this command, pick the longest one
            if matches:
                matching_patterns = matches.keys()
                matching_patterns.sort(key=len, reverse=True)
                action, groupdict = matches[matching_patterns[0]]

                event = Event(**groupdict)
        else:
            # Assume it's an action
            action = command_or_action
            event = Event(**kwargs)

        if not event:
            self.entity.tell(random.choice(('What?', 'Eh?', 'Come again?', 'Unknown command.')))
            return

        event.actor = self.entity
        for hook_point in action(event):
            if isinstance(hook_point, basestring):
                hook_type, witnesses = hook_point, []
            else:
                hook_type, witnesses = hook_point

            # TODO: This iterates over every aspect... but we know (or
            # should know) which aspects hook which actions. We should only
            # iterate over those aspect instances
            for witness in witnesses:
                for aspect in witness.aspects:
                    hooks = aspect.HOOKS.get(hook_type, {}).get(action, [])
                    for hook in hooks:
                        hook(aspect, event)


class DisambiguateMode(Mode):
    def __init__(self, entity, previous_mode, options, callback, arguments, index):
        self.entity = entity
        self.previous_mode = previous_mode
        self.callback = callback
        self.arguments = list(arguments)
        self.options = options
        self.index = index

    def to_dict(self):
        return {
            'previous_mode': self.previous_mode.to_dict(),
            'callback': self.callback,
            'arguments': self.arguments,
            'options': self.options,
            'index': self.index,
        }

    @classmethod
    def from_dict(cls, entity, dict_):
        previous_mode_dict = dict_['previous_mode']
        previous_mode_name = previous_mode_dict.pop('name')
        return cls(
            entity,
            Mode.class_from_name(previous_mode_name).from_dict(entity, previous_mode_dict),
            dict_['options'],
            dict_['callback'],
            dict_['arguments'],
            dict_['index'],
        )

    def perform(self, command):
        self.entity.mode = self.previous_mode

        option_index = int_or_none(command)

        if option_index is not None and 0 < option_index <= len(self.options):
            option = self.options[option_index - 1]
            self.arguments[self.index] = option
            getattr(self.entity, self.callback)(*self.arguments)
            return

        self.entity.mode.perform(command)
