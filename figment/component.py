class Component:
    ticking = False

    def __init__(self):
        self.entity = None

    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, dict_):
        return cls(**dict_)

    def attach(self, entity):
        self.entity = entity

    def detach(self):
        self.entity = None

    def tick(self):
        return
