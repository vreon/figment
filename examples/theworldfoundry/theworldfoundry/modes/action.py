import re
import random
from figment import Mode


class DisambiguationMode(Mode):
    def __init__(self, action_name, argument_name, kwargs, choices):
        self.action_name = action_name
        self.argument_name = argument_name
        self.kwargs = kwargs
        self.choices = choices

    def to_dict(self):
        return {
            'action_name': self.action_name,
            'argument_name': self.argument_name,
            'kwargs': self.kwargs,
            'choices': self.choices,
        }

    @classmethod
    def from_dict(cls, dict_):
        return cls(
            dict_['action_name'],
            dict_['argument_name'],
            dict_['kwargs'],
            dict_['choices'],
        )

    def perform(self, entity, command_or_index):
        entity.mode = ActionMode()

        try:
            command_or_index = int(command_or_index.strip())
            if not 0 < command_or_index <= len(self.choices):
                raise ValueError
        except ValueError:
            entity.perform(command_or_index)
            return

        action = ActionMode.ACTIONS_BY_NAME[self.action_name]
        self.kwargs[self.argument_name] = self.choices[command_or_index - 1]
        action(entity, **self.kwargs)


class ActionMode(Mode):
    ACTIONS_BY_REGEX = {}
    ACTIONS_BY_NAME = {}

    @classmethod
    def action(cls, regex):
        def register(func):
            cls.ACTIONS_BY_REGEX[regex] = func
            cls.ACTIONS_BY_NAME[func.__name__] = func
            return func
        return register

    def perform(self, entity, command_or_action, **kwargs):
        action = None

        if callable(command_or_action):
            action = command_or_action
        else:
            command = ' '.join(command_or_action.strip().split())
            matches = {}
            for pattern, matched_action in ActionMode.ACTIONS_BY_REGEX.items():
                match = re.match(pattern, command)
                if match:
                    matches[pattern] = (matched_action, match.groupdict())

            # If multiple patterns match this command, pick the longest one
            if matches:
                matching_patterns = matches.keys()
                matching_patterns.sort(key=len, reverse=True)
                action, kwargs = matches[matching_patterns[0]]

        if not action:
            entity.tell('Unknown command.')
            return

        action(entity, **kwargs)
