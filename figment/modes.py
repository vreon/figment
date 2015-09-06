import re
import random
from figment.component import Component
from figment.event import Event

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

    @classmethod
    def from_dict(cls, dict_):
        return cls()

    def to_dict(self):
        return {}

    def perform(self, entity, command):
        raise NotImplementedError


class ExploreMode(Mode):
    def perform(self, entity, command_or_action, **kwargs):
        event = None
        action = None

        if isinstance(command_or_action, basestring):
            command = ' '.join(command_or_action.strip().split())
            matches = {}
            for pattern, action in Component.ACTIONS.items():
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
            entity.tell('Unknown command.')
            return

        event.actor = entity
        for hook_point in action(event) or []:
            if isinstance(hook_point, basestring):
                hook_type, witnesses = hook_point, []
            else:
                hook_type, witnesses = hook_point

            # TODO: This iterates over every component... but we know (or
            # should know) which components hook which actions. We should only
            # iterate over those component instances
            for witness in witnesses:
                for component in witness.components:
                    hooks = component.HOOKS.get(hook_type, {}).get(action, [])
                    for hook in hooks:
                        hook(component, event)


class DebugMode(Mode):
    """
    A mode to test mode switching.
    """
    def __init__(self, num_commands=0):
        super(DebugMode, self).__init__()
        self.num_commands = num_commands

    def perform(self, entity, command):
        if command == 'stop':
            entity.tell('OK.')
            entity.mode = ExploreMode()
        else:
            self.num_commands += 1
            entity.tell('You said: {} ({})'.format(command, self.num_commands))

    def to_dict(self):
        return {
            'num_commands': self.num_commands
        }

    @classmethod
    def from_dict(cls, dict_):
        return cls(
            num_commands=dict_['num_commands']
        )
