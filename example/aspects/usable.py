from schema import EntityPlugin, before, after, action
from plugins import Positioned

class Usable(EntityPlugin):
    """Provides a 'use' hook for entities."""

    requires = [Positioned]

    @action(r'^use (?P<target>.+)$')
    def use(self, event):
        target = self.pick_nearby_inventory(event.target)
        if not target:
            return

        event.before()

        if not event.prevented:
            self.tell('Nothing happens.')

    @action(r'^use (?P<item>.+) on (?P<target>.+)')
    def use_on(self, event):
        item = self.pick_nearby_inventory(event.item)
        if not item:
            return

        target = self.pick_nearby_inventory(event.target)
        if not target:
            return

        event.before()

        if not event.prevented:
            self.tell('Nothing happens.')
