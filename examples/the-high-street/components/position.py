import string
from figment import Component, Entity, action
from figment.utils import upper_first, indent

def to_id(entity_or_id):
    if isinstance(entity_or_id, Entity):
        return entity_or_id.id
    return entity_or_id


def to_entity(entity_or_id):
    if isinstance(entity_or_id, Entity):
        return entity_or_id
    return Entity.get(entity_or_id)


class Position(Component):
    def __init__(self, container_id=None, is_container=False, is_carriable=False, is_enterable=False, is_visible=True):
        self.container_id = container_id
        self.is_container = is_container
        self.is_carriable = is_carriable
        self.is_enterable = is_enterable
        self.is_visible = is_visible

        self._contents = set()
        self._exits = {}

    def to_dict(self):
        return {
            'is_container': self.is_container,
            'container_id': self.container_id,
            'is_carriable': self.is_carriable,
            'is_enterable': self.is_enterable,
            'is_visible': self.is_visible,
            'contents': list(self._contents),
            'exits': self._exits,
        }

    @classmethod
    def from_dict(cls, dict_):
        self = cls()

        self.container_id = dict_['container_id']
        self.is_container = dict_['is_container']
        self.is_carriable = dict_['is_carriable']
        self.is_enterable = dict_['is_enterable']
        self.is_visible = dict_['is_visible']
        self._contents = set(dict_['contents'])
        self._exits = dict_['exits']

        return self

    def attach(self, entity):
        super(Position, self).attach(entity)

        container = self.container
        if container:
            container.Position._contents.add(self.entity.id)

    def detach(self):
        for item in self.contents():
            item.Position.container_id = self.container_id

        container = self.container
        if container:
            container.Position._contents.remove(self.entity.id)

        self._contents = set()
        self._exits = {}

        super(Position, self).detach()

    #########################
    # Selection
    #########################

    def nearby(self):
        return set(entity for entity in self.container.Position.contents() if not entity == self.entity)

    def pick(self, selector, entity_set):
        """
        Pick entities from a set by selector (name or ID). In most cases you
        should use one of the higher-level pick_* functions.
        """
        if selector.lower() in ('self', 'me', 'myself'):
            return set((self.entity,))

        return set(e for e in entity_set if (selector.lower() in e.name.lower() or selector == e.id) and e.Position.is_visible)

    def pick_interactively(self, selector, entity_set, area='in that area'):
        """
        Possibly target an object, and possibly enter a disambiguation menu
        """
        matches = self.pick(selector, entity_set)
        num_matches = len(matches)

        if num_matches == 0:
            self.entity.tell("There's no {0} {1}.".format(selector, area))
        elif num_matches == 1:
            return matches.pop()
        else:
            self.entity.tell("Which '{0}' do you mean?".format(selector))
            targets = []
            for index, entity in enumerate(matches):
                position = 'in inventory' if entity.Position.container == self.entity else 'nearby'
                self.entity.tell(indent('{0}. {1.name} ({2})'.format(index + 1, entity, position)))
                targets.append(entity.id)
            # raise AmbiguousSelector(selector, targets)

    def pick_nearby(self, selector):
        return self.pick_interactively(selector, self.nearby(), area='nearby')

    def pick_inventory(self, selector):
        return self.pick_interactively(selector, self.contents(), area='in your inventory')

    def pick_from(self, selector, container):
        return self.pick_interactively(selector, container.Position.contents(), area='in {0.name}'.format(container))

    def pick_nearby_inventory(self, selector):
        return self.pick_interactively(selector, self.contents() | self.nearby(), area='nearby')

    #########################
    # Position, contents
    #########################

    @staticmethod
    def move(entity, container):
        old_container = entity.Position.container

        if old_container:
            old_container.Position._contents.remove(entity.id)

        container.Position._contents.add(entity.id)
        entity.Position.container_id = container.id

    def store(self, entity):
        Position.move(entity, self.entity)

    def unstore(self, entity):
        Position.move(entity, self.container)

    # TODO: This should be set at attach time
    @property
    def container(self):
        if self.container_id:
            return self.entity.zone.get(self.container_id)

    # TODO: This should be set at attach time
    def contents(self):
        return set(self.entity.zone.get(id) for id in self._contents)

    # TODO: This should be set at attach time
    def exits(self):
        resolved_exits = {}
        for name, selector in self._exits.items():
            if selector == '.':
                id = self.entity.id
            elif selector == '..':
                id = self.container_id
            else:
                id = selector
            resolved_exits[name] = self.entity.zone.get(id)
        return resolved_exits

    def link(self, direction, destination, back_direction=None):
        # NOTE: This depends on _to_id not transforming values like . or ..
        destination_id = to_id(destination)
        self._exits[direction] = destination_id
        if back_direction and not destination in ('.', '..'):
            destination = to_entity(destination)
            destination.Position._exits[back_direction] = self.entity.id

    def unlink(self, direction, destination, back_direction=None):
        # NOTE: This depends on _to_id not transforming values like . or ..
        destination_id = to_id(destination)
        self._exits.pop(direction, None)
        if back_direction and not destination in ('.', '..'):
            destination = to_entity(destination)
            destination.Position._exits.pop(back_direction, None)

    #########################
    # Communication
    #########################

    def announce(self, message):
        """Send text to this entity's contents."""
        for listener in self.contents():
            listener.tell(message)

    def emit(self, sound, exclude=set()):
        """Send text to entities nearby this one."""
        nearby = self.nearby()
        try:
            exclude = set(exclude)
        except TypeError:
            exclude = set([exclude])
        exclude.add(self.entity)
        listeners = nearby - exclude
        for listener in listeners:
            listener.tell(sound)

    def tell_surroundings(self):
        room = self.container

        messages = [string.capwords(room.name), room.desc]

        exits = room.Position.exits()
        if exits:
            messages.append('Exits:')
            for direction, destination in exits.items():
                messages.append(indent('{0}: {1}'.format(direction, destination.name)))

        entities_nearby = [e for e in self.nearby() if e.Position.is_visible]
        if entities_nearby:
            messages.append('Things nearby:')
            for entity in entities_nearby:
                messages.append(indent(entity.name))

        self.entity.tell('\n'.join(messages))

    #########################
    # Actions
    #########################

    @action(r'^s(?:ay)? (?P<message>.+)$')
    def say(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to do that.")
            return

        message = upper_first(event.message.strip().replace('"', "'"))

        if not message[-1] in ('.', '?', '!'):
            message += '.'

        yield 'before', event.actor.Position.nearby()
        if event.data.get('prevented'):
            return

        event.actor.tell('You say: "{0}"'.format(message))
        event.actor.Position.emit('{0.Name} says: "{1}"'.format(event.actor, message))

    @action(r'^l(?:ook)?(?: around)?$')
    def look(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to do that.")
            return

        yield 'before'
        if event.data.get('prevented'):
            return

        event.actor.Position.emit('{0.Name} looks around.'.format(event.actor))
        event.actor.Position.tell_surroundings()

    @action(r'^l(?:ook)? (?:in(?:to|side(?: of)?)?) (?P<selector>.+)$')
    def look_in(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to do that.")
            return

        event.target = event.actor.Position.pick_nearby_inventory(event.selector)
        if not event.target:
            return

        if not event.target.has_component(Position) or not event.target.Position.is_container:
            event.actor.tell("You can't look inside of that.")
            return

        yield 'before'
        if event.data.get('prevented'):
            return

        event.actor.tell('Contents:')

        contents = [e for e in event.target.Position.contents() if e.Position.is_visible]
        if contents:
            for item in contents:
                event.actor.tell(indent('{0.name}'.format(item)))
        else:
            event.actor.tell(indent('nothing'))

    @action(r'^(?:ex(?:amine)?|l(?:ook)?) (?:at )?(?P<selector>.+)$')
    def look_at(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to do that.")
            return

        event.target = event.actor.Position.pick_nearby_inventory(event.selector)
        if not event.target:
            return

        yield 'before'
        if event.data.get('prevented'):
            return

        event.actor.tell(event.target.desc)
        event.actor.Position.emit('{0.Name} looks at {1}.'.format(event.actor, event.target.name), exclude=event.target)
        event.target.tell('{0.Name} looks at you.'.format(event.actor))

    @action('^(?:get|take|pick up) (?P<selector>.+)$')
    def get(event):
        if not event.actor.has_component(Position) or not event.actor.Position.is_container:
            event.actor.tell("You're unable to do that.")
            return

        event.target = event.actor.Position.pick_nearby(event.selector)
        if not event.target:
            return

        if event.target == event.actor:
            event.actor.tell("You can't put yourself in your inventory.")
            return

        if not event.target.has_component(Position) or not event.target.Position.is_carriable:
            event.actor.tell("That can't be carried.")
            return

        yield 'before'
        if event.data.get('prevented'):
            return

        event.actor.tell('You pick up {0.name}.'.format(event.target))
        event.actor.Position.emit('{0.Name} picks up {1.name}.'.format(event.actor, event.target), exclude=event.target)
        event.target.tell('{0.Name} picks you up.'.format(event.actor))
        event.actor.Position.store(event.target)

    @action('^(?:get|take|pick up) (?P<target_selector>.+) from (?P<container_selector>.+)$')
    def get_from(event):
        if not event.actor.has_component(Position) or not event.actor.Position.is_container:
            event.actor.tell("You're unable to hold items.")
            return

        event.container = event.actor.Position.pick_nearby_inventory(event.container_selector)
        if not event.container:
            return

        if event.container == event.actor:
            event.actor.tell("You can't get things from your inventory, they'd just go right back in!")
            return

        if not event.container.has_component(Position) or not event.container.Position.is_container:
            event.actor.tell("{0.Name} can't hold items.".format(event.container))
            return

        event.target = event.actor.Position.pick_from(event.target_selector, event.container)
        if not event.target:
            return

        if event.target == event.actor:
            event.actor.tell("You can't put yourself in your inventory.")
            return

        if not event.target.has_component(Position):
            event.actor.tell("You can't take {0.name} from {1.name}.".format(event.target, event.container))
            return

        yield 'before'
        if event.data.get('prevented'):
            return

        event.actor.tell('You take {0.name} from {1.name}.'.format(event.target, event.container))
        event.actor.Position.emit('{0.Name} takes {1.name} from {2.name}.'.format(event.actor, event.target, event.container), exclude=(event.target, event.container))
        event.container.tell('{0.Name} takes {1.name} from you.'.format(event.actor, event.target))
        event.target.tell('{0.Name} takes you from {1.name}.'.format(event.actor, event.container))
        event.actor.Position.store(event.target)

    @action(r'^put (?P<target_selector>.+) (?:in(?:to|side(?: of)?)?) (?P<container_selector>.+)$')
    def put_in(event):
        if not event.actor.has_component(Position) or not event.actor.Position.is_container:
            event.actor.tell("You're unable to hold things.")
            return

        event.target = event.actor.Position.pick_nearby_inventory(event.target_selector)
        if not event.target:
            return

        if not event.target.has_component(Position):
            event.actor.tell("You can't put {0.name} into anything.")
            return

        event.container = event.actor.Position.pick_nearby_inventory(event.container_selector)
        if not event.container:
            return

        if not event.container.has_component(Position) or not event.container.Position.is_container:
            event.actor.tell("{0.Name} can't hold things.".format(event.container))
            return

        yield 'before'
        if event.data.get('prevented'):
            return

        event.actor.tell('You put {0.name} in {1.name}.'.format(event.target, event.container))
        event.actor.Position.emit('{0.Name} puts {1.name} in {2.name}.'.format(event.actor, event.target, event.container), exclude=(event.target, event.container))
        event.container.tell('{0.Name} puts {1.name} in your inventory.'.format(event.actor, event.target))
        event.target.tell('{0.Name} puts you in {1.name}.'.format(event.actor, event.container))
        event.container.Position.store(event.target)

    @action(r'^drop (?P<selector>.+)$')
    def drop(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to drop things.")
            return

        event.target = event.actor.Position.pick_inventory(event.selector)
        if not event.target:
            return

        # TODO: other nearby stuff
        yield 'before', [event.target]
        if event.data.get('prevented'):
            return

        event.actor.Position.unstore(event.target)
        event.actor.tell('You drop {0.name}.'.format(event.target))
        event.actor.Position.emit('{0.Name} drops {1.name}.'.format(event.actor, event.target), exclude=event.target)
        event.target.tell('{0.Name} drops you.'.format(event.actor))

    @action('^(?:w(?:alk)?|go) (?P<direction>.+)$')
    def walk(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to move.")
            return

        room = event.actor.Position.container

        # Actor is hanging out at the top level, or room is in a bad state
        if not room or not room.has_component(Position):
            event.actor.tell("You're unable to leave this place.")
            return

        exits = room.Position.exits()
        if not exits:
            event.actor.tell("There don't seem to be any exits here.")
            return

        for exit_name in exits:
            if event.direction.lower() == exit_name.lower():
                event.direction = exit_name
                break
        else:
            event.actor.tell("You're unable to go that way.")
            return

        destination = exits[event.direction]

        # Ensure the destination is still a container
        if not destination or not destination.has_component(Position) or not destination.Position.is_container:
            event.actor.tell("You're unable to go that way.")
            return

        yield 'before'
        if event.data.get('prevented'):
            return

        event.actor.tell('You travel {0}.'.format(event.direction))
        event.actor.Position.emit('{0.Name} travels {1} to {2.name}.'.format(event.actor, event.direction, destination))
        destination.Position.announce('{0.Name} arrives from {1.name}.'.format(event.actor, room))
        destination.Position.store(event.actor)

        event.actor.Position.tell_surroundings()

    @action(r'^enter (?P<selector>.+)$')
    def enter(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to move.")
            return

        room = event.actor.Position.container

        # Actor is hanging out at the top level, or room is in a bad state
        if not room or not room.has_component(Position):
            event.actor.tell("You're unable to leave this place.")
            return

        event.container = event.actor.Position.pick_nearby(event.selector)
        if not event.container:
            return

        if not event.container.has_component(Position) or not event.container.Position.is_container or not event.container.Position.is_enterable:
            event.actor.tell("You can't enter that.")
            return

        yield 'before'
        if event.prevented:
            return

        event.actor.tell('You enter {0.name}.'.format(event.container))
        event.actor.Position.emit('{0.Name} enters {1.name}.'.format(event.actor, event.container))
        event.container.Position.announce('{0.Name} arrives from {1.name}.'.format(event.actor, room))
        event.container.Position.store(event.actor)

        event.actor.Position.tell_surroundings()

    ##########################
    # Aliases and shortcuts
    ##########################

    @action('^(?:i|inv|inventory)$')
    def tell_inventory(event):
        return event.actor.perform('look in self')

    @action('^n(?:orth)?$')
    def go_north(event):
        return event.actor.perform('go north')

    @action('^s(?:outh)?$')
    def go_south(event):
        return event.actor.perform('go south')

    @action('^e(?:ast)?$')
    def go_east(event):
        return event.actor.perform('go east')

    @action('^w(?:est)?$')
    def go_west(event):
        return event.actor.perform('go west')

    @action('^(?:ne|northeast)?$')
    def go_northeast(event):
        return event.actor.perform('go northeast')

    @action('^(?:nw|northwest)?$')
    def go_northwest(event):
        return event.actor.perform('go northwest')

    @action('^(?:se|southeast)?$')
    def go_southeast(event):
        return event.actor.perform('go southeast')

    @action('^(?:sw|southwest)?$')
    def go_southwest(event):
        return event.actor.perform('go southwest')

    @action('^u(?:p)?$')
    def go_up(event):
        return event.actor.perform('go up')

    @action('^d(?:own)?$')
    def go_down(event):
        return event.actor.perform('go down')
