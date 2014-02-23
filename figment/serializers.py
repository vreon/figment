"""
Defines a unified interface for saving and loading stuff from strings.
"""

# Because serialization libraries other than JSON are optional dependencies,
# imports should be at method scope so they don't get executed until needed.

# TODO: Unify serialize/unserialize errors so they can be caught by the caller


class Serializer(object):
    extension = None

    @staticmethod
    def serialize(data):
        raise NotImplementedError

    @staticmethod
    def unserialize(data):
        raise NotImplementedError


class JSONSerializer(Serializer):
    extension = 'json'

    @staticmethod
    def serialize(data):
        import json
        return json.dumps(data)

    @staticmethod
    def unserialize(data):
        import json
        return json.loads(data)


class YAMLSerializer(Serializer):
    extension = 'yaml'

    @staticmethod
    def serialize(data):
        import yaml
        return yaml.dump(data)

    @staticmethod
    def unserialize(data):
        import yaml
        return yaml.safe_load(data)


SERIALIZERS = {
    'json': JSONSerializer,
    'yaml': YAMLSerializer,
}
