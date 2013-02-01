from schema.entity import Entity

class Event(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.action = None
        self.actor = None
        self.prevented = False

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

    def end(self):
        # TODO: Find all witnesses of this event and pass self to the hooks
        pass

    def witnesses(self):
        # TODO: How should this be handled?
        pass
