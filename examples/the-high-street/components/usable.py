from figment import Component, action
from components import Position


class Usable(Component):
    """Provides a 'use' hook for entities."""

    @action(r'^use (?P<selector>.+)$')
    def use(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to do that.")
            return

        event.target = event.actor.Position.pick_nearby_inventory(event.selector)
        if not event.target:
            return

        event.actor.tell("You can't use that.")

    @action(r'^use (?P<item_selector>.+) on (?P<target_selector>.+)')
    def use_on(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to do that.")
            return

        event.item = event.actor.Position.pick_nearby_inventory(event.item_selector)
        if not event.item:
            return

        event.target = event.actor.Position.pick_nearby_inventory(event.target_selector)
        if not event.target:
            return

        event.actor.tell('Nothing happens.')
