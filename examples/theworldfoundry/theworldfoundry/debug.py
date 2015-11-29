from figment.debug import Renderer as FigmentRenderer
import json

class Renderer(FigmentRenderer):
    def render(self, message):
        if isinstance(message, dict):
            return getattr(self, 'render_' + message['type'], self.render_unknown)(message)
        else:
            # Handle legacy string-style messages
            message = {'type': 'message', 'text': message}
            return self.render(message)

    def render_message(self, message):
        return message['text']

    def render_unknown(self, message):
        return json.dumps(message)
