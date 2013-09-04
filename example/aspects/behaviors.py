from figment.entity import Entity, start_room
import random

class Behavior(Entity):
    def on_tick(self):
        pass
    def before_look(self, actor):
        return False
    def after_look(self, actor):
        return False
    def before_look_in(self, actor, target):
        return False
    def after_look_in(self, actor, target):
        return False
    def before_look_at(self, actor, target):
        return False
    def after_look_at(self, actor, target):
        return False
    def before_get(self, actor, target):
        return False
    def after_get(self, actor, target):
        return False
    def before_get_from(self, actor, target, container):
        return False
    def after_get_from(self, actor, target, container):
        return False
    def before_put_in(self, actor, item, container):
        return False
    def after_put_in(self, actor, item, container):
        return False
    def before_use(self, actor, target):
        return False
    def before_use_on(self, actor, item, target):
        return False
    def before_drop(self, actor, target):
        return False
    def after_drop(self, actor, target):
        return False
    def before_say(self, actor, message):
        return False
    def after_say(self, actor, message):
        return False
    def before_walk(self, actor, direction, destination):
        return False
    def after_walk(self, actor, direction, source):
        return False

class StickyBlob(Behavior):
    """Has a one-in-five chance of dropping successfully."""
    def before_drop(self, actor, target):
        if self == target:
            if random.randint(1, 5) != 1:
                actor.tell('You try to drop {0.name}, but it sticks to your hand.'.format(self))
                return True
        return False

class Hubstone(Behavior):
    """A usable item that teleports you home."""
    def before_drop(self, actor, target):
        if self == target:
            actor.tell("You shouldn't get rid of this; it's very important.")
            return True
        return False

    def before_put_in(self, actor, target, container):
        if self == target:
            actor.tell("You shouldn't get rid of this; it's very important.")
            return True
        return False

    def before_get(self, actor, target):
        if self == target:
            actor.tell('{0.Name} resists your attempt to grab it.'.format(self))
            return True
        return False

    def before_get_from(self, actor, target, container):
        if self == target:
            actor.tell('{0.Name} resists your attempt to grab it.'.format(self))
            return True
        return False

    def before_use(self, actor, target):
        if self == target:
            actor.tell('{0.Name} glows vibrantly.'.format(self))
            actor.tell('Your vision is obscured by a brief flash of light.')
            actor.emit('{0.Name} vanishes in a vibrant flash of light.'.format(actor))
            start_room().store(actor)
            actor.tell_surroundings()
            return True
        return False

class RoomCreator(Behavior):
    """A totally broken item that creates new rooms."""
    def before_use(self, actor, target):
        if self == target:
            room = actor.container

            direction_pairs = (
                ('north', 'south'),
                ('east', 'west'),
                ('south', 'north'),
                ('west', 'east'),
                ('up', 'down'),
                ('down', 'up'),
            )

            direction, backlink = random.choice(direction_pairs)
            if direction in room.exits():
                return False

            actor.emit('{0.Name} activates {1.name}.'.format(actor, self))
            room.announce('The room shakes violently.')

            letter = random.choice((
                'Alpha', 'Beta', 'Delta', 'Gamma', 'Epsilon', 'Sigma', 'Tau'
            ))
            number = random.choice((
                'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            ))

            new_room = Entity.new(
                'Subspace Volume {0}-{1}'.format(letter, number),
                'A rift in the space-time continuum.',
                is_container = True,
            )

            room.link(direction, new_room, backlink)

            room.announce('A path to {0.name} appears {1}.'.format(new_room, direction))

            return True
        return False

BEHAVIORS = {
    'stickyblob': StickyBlob,
    'hubstone': Hubstone,
    'roomcreator': RoomCreator,
}
