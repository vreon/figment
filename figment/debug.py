import json


class Renderer:
    def render(self, message):
        raise NotImplementedError


class DefaultRenderer(Renderer):
    def render(self, message):
        return json.dumps(message)
