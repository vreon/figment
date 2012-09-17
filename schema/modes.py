import re
import random
from schema.models import redis, ACTIONS
from schema.utils import int_or_none


class Mode(object):
    def __init__(self, entity):
        self.entity = entity

    def perform(self, command):
        raise NotImplementedError


class ExploreMode(Mode):
    name = 'explore'

    def perform(self, command):
        matches = {}
        for pattern, action in ACTIONS.iteritems():
            match = re.match(pattern, command)
            if match:
                matches[pattern] = (action, match.groups())

        # If multiple patterns match this command, pick the longest one
        if matches:
            matching_patterns = matches.keys()
            matching_patterns.sort(key=len, reverse=True)
            action, groups = matches[matching_patterns[0]]
            action(self.entity, *groups)
        else:
            self.entity.tell(random.choice(('What?', 'Eh?', 'Come again?', 'Unknown command.')))


class DisambiguateMode(Mode):
    name = 'disambiguate'

    def __init__(self, entity, callback, arguments, index):
        self.entity = entity
        self.callback = callback
        self.arguments = list(arguments)
        self.index = index

    def perform(self, command):
        self.entity.mode = ExploreMode(self.entity)

        option_index = int_or_none(command)
        options = self.entity._recently_seen
        self.entity._recently_seen = []

        if option_index is not None and 0 < option_index <= len(options):
            option = options[option_index - 1]
            self.arguments[self.index] = option
            getattr(self.entity, self.callback)(*self.arguments)
            return

        self.entity.mode.perform(command)
