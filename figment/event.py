class Event(object):
    def __init__(self, **kwargs):
        self.action = None
        self.actor = None
        self.data = {}
        self.__dict__.update(kwargs)

    # This is probably considered unpythonic, but it makes the event API easier
    # to use, so I'm doin' it
    def __getattr__(self, key):
        return None
