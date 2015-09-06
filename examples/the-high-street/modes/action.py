import re
import random
from figment import Mode


class ActionMode(Mode):
    ACTIONS = {}

    @classmethod
    def action(cls, regex):
        def register(func):
            cls.ACTIONS[regex] = func
            return func
        return register

    def perform(self, entity, command_or_action, **kwargs):
        action = None

        if callable(command_or_action):
            action = command_or_action
        else:
            command = ' '.join(command_or_action.strip().split())
            matches = {}
            for pattern, action in ActionMode.ACTIONS.items():
                match = re.match(pattern, command)
                if match:
                    matches[pattern] = (action, match.groupdict())

            # If multiple patterns match this command, pick the longest one
            if matches:
                matching_patterns = matches.keys()
                matching_patterns.sort(key=len, reverse=True)
                action, kwargs = matches[matching_patterns[0]]

        if not action:
            entity.tell('Unknown command.')
            return

        action(entity, **kwargs)
