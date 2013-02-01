import re
import random
from schema.entity import redis
from schema.aspect import Aspect
from schema.event import Event
from schema.utils import int_or_none

def _mode_from_dict(entity, dict_):
    return MODE_MAP[dict_['name']].from_dict(entity, dict_)

class Mode(object):
    def __init__(self, entity):
        self.entity = entity

    def perform(self, command):
        raise NotImplementedError


class ExploreMode(Mode):
    def __init__(self, entity):
        self.entity = entity

    def to_dict(self):
        return {
            'name': self.name,
        }

    @classmethod
    def from_dict(cls, entity, dict_):
        return cls(entity)

    def perform(self, command):
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
            event.actor = self.entity
            event.action = action
            action(event)
        else:
            self.entity.tell(random.choice(('What?', 'Eh?', 'Come again?', 'Unknown command.')))


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
            'name': self.name,
            'previous_mode': self.previous_mode.to_dict(),
            'callback': self.callback,
            'arguments': self.arguments,
            'options': self.options,
            'index': self.index,
        }

    @classmethod
    def from_dict(cls, entity, dict_):
        return cls(
            entity,
            _mode_from_dict(entity, dict_['previous_mode']),
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

MODE_MAP = {
    'explore': ExploreMode,
    'disambiguate': DisambiguateMode,
}
for k, v in MODE_MAP.items():
    v.name = k
