from schema.entity import Entity

class Event(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.action = None
        self.actor = None
        self.prevented = False

    # This is probably considered unpythonic, but it makes the event API easier
    # to use, so I'm doin' it
    def __getattr__(self, key):
        return None

    def prevent_default(self):
        self.prevented = True
        # TODO: this is too specific to the before hook
        # How would someone "prevent" a custom hook?

    def trigger(self, hook_type):
        for witness in self.witnesses():
            # TODO: This iterates over every aspect... but we know (or
            # should know) which aspects hook which actions. We should only
            # iterate over those aspect instances
            for aspect in witness.aspects:
                hooks = aspect.HOOKS.get(hook_type, {}).get(self.action, [])
                for hook in hooks:
                    hook(aspect, self)

    def witnesses(self):
        # If an event fires in a Schema world, but no Entities are around to
        # witness it ... did it really happen?
        return []
