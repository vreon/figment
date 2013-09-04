from figment import EntityPlugin, before, after
from .positioned import Positioned
from .important import Important
from .usable import Usable

class Hubstone(EntityPlugin):
    """A usable item that teleports you home."""
    includes = [Important]

    def __init__(self, home):
        self.home = home

    def to_dict(self):
        return {
            'home': self.home,
        }

    @before(Usable.use)
    def activate(self, actor, target):
        if self == target:
            actor.tell('{0.Name} glows vibrantly.'.format(self))
            actor.tell('Your vision is obscured by a brief flash of light.')
            actor.emit('{0.Name} vanishes in a vibrant flash of light.'.format(actor))
            start_room().store(actor)
            actor.tell_surroundings()
            return True
        return False
