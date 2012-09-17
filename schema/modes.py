import re
import random
from schema.models import redis, ACTIONS
from schema.utils import int_or_none


class Mode(object):
    def __init__(self, entity):
        self.entity = entity

    def bind(self):
        redis.hset(self.entity.key, 'mode', self.name)

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

    @property
    def arguments_key(self):
        return 'entity:%s:mode:%s:arguments' % (self.entity.id, self.name)

    @property
    def callback_key(self):
        return 'mode:%s:callback' % self.name

    @property
    def index_key(self):
        return 'mode:%s:index' % self.name

    def bind(self, callback, args, index):
        super(DisambiguateMode, self).bind()
        pipe = redis.pipeline()
        for arg in args:
            pipe.rpush(self.arguments_key, arg)
        pipe.hset(self.entity.key, self.callback_key, callback.__name__)
        pipe.hset(self.entity.key, self.index_key, index)
        pipe.execute()

    def perform(self, command):
        explore_fallback = ExploreMode(self.entity)
        explore_fallback.bind()

        option_index = int_or_none(command)
        menu_index = int(redis.hget(self.entity.key, self.index_key))
        callback = redis.hget(self.entity.key, self.callback_key)
        arguments = redis.lrange(self.arguments_key, 0, -1)
        options = redis.lrange(self.entity.recently_seen_key, 0, -1)

        pipe = redis.pipeline()
        pipe.delete(self.entity.recently_seen_key)
        pipe.delete(self.arguments_key)
        pipe.hdel(self.entity.key, self.callback_key, self.index_key)
        pipe.execute()

        if option_index is not None and 0 < option_index <= len(options):
            option = options[option_index - 1]
            arguments[menu_index] = option
            getattr(self.entity, callback)(*arguments)
            return

        explore_fallback.perform(command)


MODE_MAP = {
    'explore': ExploreMode,
    'disambiguate': DisambiguateMode,
}
