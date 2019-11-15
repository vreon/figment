class Mode:
    @classmethod
    def from_dict(cls, dict_):
        return cls()

    def to_dict(self):
        return {}

    def perform(self, entity, command):
        raise NotImplementedError
