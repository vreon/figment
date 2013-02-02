from schema import Event, Aspect, action
from . import Positioned

class Usable(Aspect):
    """Provides a 'use' hook for entities."""

    requires = [Positioned]

    @action(r'^use (?P<target>.+)$')
    def use(event):
        target = event.actor.Positioned.pick_nearby_inventory(event.target)
        if not target:
            return

        event.trigger('before')
        if not event.prevented:
            event.actor.tell("You can't use that.")

    @action(r'^use (?P<item>.+) on (?P<target>.+)')
    def use_on(event):
        item = event.actor.Positioned.pick_nearby_inventory(event.item)
        if not item:
            return

        target = event.actor.Positioned.pick_nearby_inventory(event.target)
        if not target:
            return

        event.trigger('before')
        if not event.prevented:
            self.tell('Nothing happens.')
