import re
import random
from figment.component import Component
from figment.event import Event

# For Python 3 compatibility
try:
    basestring
except NameError:
    basestring = (str, bytes)


class Mode(object):
    @classmethod
    def from_dict(cls, dict_):
        return cls()

    def to_dict(self):
        return {}

    def perform(self, entity, command):
        raise NotImplementedError


class ActionMode(Mode):
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
        action(event)


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
            entity.mode = ActionMode()
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
