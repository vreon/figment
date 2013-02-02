from schema import Entity, Aspect, action, jug
from schema.utils import upper_first, indent, to_id, to_entity

class Positioned(Aspect):
    def __init__(self, is_container=False, is_carriable=False, is_enterable=False, is_invisible=False):
        self.container_id = None
        self.is_container = is_container
        self.is_carriable = is_carriable
        self.is_enterable = is_enterable
        self.is_invisible = is_invisible

        self._contents = set()
        self._exits = {}

    def to_dict(self):
        return {
            'is_container': self.is_container,
            'container_id': self.container_id,
            'is_carriable': self.is_carriable,
            'is_enterable': self.is_enterable,
            'is_invisible': self.is_invisible,
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
        self.is_invisible = dict_['is_invisible']
        self._contents = set(dict_['contents'])
        self._exits = dict_['exits']

        return self

    def destroy(self):
        for item in self.contents():
            item.Positioned.container_id = self.container_id

        container = self.container
        if container:
            self.container.Positioned._contents.remove(self.entity.id)

        self._behaviors = []
        self._contents = set()
        self._exits = {}

    #########################
    # Selection
    #########################

    def nearby(self):
        return set(entity for entity in self.container.Positioned.contents() if not entity == self.entity)

    def pick(self, descriptor, entity_set):
        """
        Pick entities from a set by descriptor (name or ID). In most cases you
        should use one of the higher-level pick_* functions.
        """
        if descriptor in ('self', 'me', 'myself'):
            return set((self.entity,))

        return set(e for e in entity_set if (descriptor.lower() in e.name.lower() or descriptor == e.id) and not e.Positioned.is_invisible)

    def pick_interactively(self, descriptor, entity_set, area='in that area'):
        """
        Possibly target an object, and possibly enter interactive disambiguation mode.
        """
        entities = self.pick(descriptor, entity_set)
        matches = len(entities)

        if matches == 0:
            self.entity.tell("There's no {0} {1}.".format(descriptor, area))
        elif matches == 1:
            return entities.pop()
        else:
            self.entity.tell("Which '{0}' do you mean?".format(descriptor.value))
            targets = []
            for index, entity in enumerate(entities):
                position = 'in inventory' if entity.Positioned.container == self.entity else 'nearby'
                self.entity.tell(indent('{0}. {1.name} ({2})'.format(index + 1, entity, position)))
                targets.append(entity.id)
            raise AmbiguousDescriptor(descriptor, targets)

    def pick_nearby(self, descriptor):
        return self.pick_interactively(descriptor, self.nearby(), area='nearby')

    def pick_inventory(self, descriptor):
        return self.pick_interactively(descriptor, self.contents(), area='in your inventory')

    def pick_from(self, descriptor, container):
        return self.pick_interactively(descriptor, container.Positioned.contents(), area='in {0.name}'.format(container))

    def pick_nearby_inventory(self, descriptor):
        return self.pick_interactively(descriptor, self.contents() | self.nearby(), area='nearby')

    #########################
    # Position, contents
    #########################

    @staticmethod
    def move(entity, container):
        old_container = entity.Positioned.container

        if old_container:
            old_container.Positioned._contents.remove(entity.id)

        container.Positioned._contents.add(entity.id)
        entity.Positioned.container_id = container.id

    def store(self, entity):
        Positioned.move(entity, self.entity)

    # TODO: Rename to drop (but collides with action of same name)
    def remove(self, entity):
        Positioned.move(entity, self.container)

    @property
    def container(self):
        if self.container_id:
            return Entity.get(self.container_id)

    def contents(self):
        return set(Entity.get(id) for id in self._contents)

    def exits(self):
        resolved_exits = {}
        for name, descriptor in self._exits.items():
            if descriptor == '.':
                id = self.entity.id
            elif descriptor == '..':
                id = self.container_id
            else:
                id = descriptor
            resolved_exits[name] = Entity.get(id)
        return resolved_exits

    def link(self, direction, destination, back_direction=None):
        # NOTE: This depends on _to_id not transforming values like . or ..
        destination_id = to_id(destination)
        self._exits[direction] = destination_id
        if back_direction and not destination in ('.', '..'):
            destination = to_entity(destination)
            destination.Positioned._exits[back_direction] = self.entity.id

    #########################
    # Communication
    #########################

    def announce(self, message):
        """Send text to this entity's contents."""
        channels = [listener.messages_key for listener in self.contents()]
        jug.publish(channels, message)

    def emit(self, sound, exclude=set()):
        """Send text to entities nearby this one."""
        nearby = self.nearby()
        try:
            exclude = set(exclude)
        except TypeError:
            exclude = set((exclude,))
        exclude.add(self.entity)
        listeners = nearby - exclude
        channels = [listener.messages_key for listener in listeners]
        jug.publish(channels, sound)

    def tell_surroundings(self):
        room = self.container

        messages = [room.name.title(), room.desc]

        exits = room.Positioned.exits()
        if exits:
            messages.append('Exits:')
            for direction, destination in exits.items():
                messages.append(indent('{0}: {1}'.format(direction, destination.name)))

        entities_nearby = [e for e in self.nearby() if not e.Positioned.is_invisible]
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
        message = upper_first(event.message.strip().replace('"', "'"))

        if not message[-1] in ('.', '?', '!'):
            message += '.'

        event.trigger('before')
        if not event.prevented:
            event.actor.tell('You say: "{0}"'.format(message))
            event.actor.Positioned.emit('{0.Name} says: "{1}"'.format(event.actor, message))

    @action(r'^l(?:ook)?(?: around)?$')
    def look(event):
        event.trigger('before')
        if not event.prevented:
            event.actor.Positioned.emit('{0.Name} looks around.'.format(event.actor))
            event.actor.Positioned.tell_surroundings()

    @action(r'^l(?:ook)? (?:in(?:to|side(?: of)?)?) (?P<descriptor>.+)$')
    def look_in(event):
        target = event.actor.Positioned.pick_nearby_inventory(event.descriptor)
        if not target:
            return

        if not target.Positioned.is_container:
            event.actor.tell("You can't look inside of that.")
            return

        event.trigger('before')
        if event.prevented:
            return

        event.actor.tell('Contents:')

        contents = [e for e in target.Positioned.contents() if not e.Positioned.is_invisible]
        if contents:
            for item in contents:
                event.actor.tell(indent('{0.name}'.format(item)))
        else:
            event.actor.tell(indent('nothing'))

    @action(r'^(?:ex(?:amine)?|l(?:ook)?) (?:at )?(?P<descriptor>.+)$')
    def look_at(event):
        target = event.actor.Positioned.pick_nearby_inventory(event.descriptor)
        if not target:
            return

        event.trigger('before')
        if event.prevented:
            return

        event.actor.tell(target.desc)
        event.actor.Positioned.emit('{0.Name} looks at {1}.'.format(event.actor, target.name), exclude=target)
        target.tell('{0.Name} looks at you.'.format(event.actor))

    @action('^(?:get|take) (?P<descriptor>.+)$')
    def get(event):
        if not event.actor.Positioned.is_container:
            event.actor.tell("You're unable to hold items.")
            return

        target = event.actor.Positioned.pick_nearby(event.descriptor)
        if not target:
            return

        if target == event.actor:
            event.actor.tell("You can't put yourself in your inventory.")
            return

        if not target.Positioned.is_carriable:
            event.actor.tell("That can't be carried.")
            return

        event.trigger('before')
        if event.prevented:
            return

        event.actor.tell('You pick up {0.name}.'.format(target))
        event.actor.Positioned.emit('{0.Name} picks up {1.name}.'.format(event.actor, target), exclude=target)
        target.tell('{0.Name} picks you up.'.format(event.actor))
        event.actor.Positioned.store(target)

    @action('^(?:get|take) (?P<target_descriptor>.+) from (?P<container_descriptor>.+)$')
    def get_from(event):
        if not event.actor.Positioned.is_container:
            event.actor.tell("You're unable to hold items.")
            return

        container = event.actor.Positioned.pick_nearby_inventory(event.container_descriptor)
        if not container:
            return

        if container == event.actor:
            event.actor.tell("You can't get things from your inventory, they'd just go right back in!")
            return

        if not container.Positioned.is_container:
            event.actor.tell("{0.Name} can't hold items.".format(container))
            return

        target = event.actor.Positioned.pick_from(event.target_descriptor, container)
        if not target:
            return

        if target == event.actor:
            event.actor.tell("You can't put yourself in your inventory.")
            return

        event.trigger('before')
        if event.prevented:
            return

        event.actor.tell('You take {0.name} from {1.name}.'.format(target, container))
        event.actor.Positioned.emit('{0.Name} takes {1.name} from {2.name}.'.format(event.actor, target, container), exclude=(target, container))
        container.tell('{0.Name} takes {1.name} from you.'.format(event.actor, target))
        target.tell('{0.Name} takes you from {1.name}.'.format(event.actor, container))
        event.actor.Positioned.store(target)

    @action(r'^put (?P<target_descriptor>.+) in (?P<container_descriptor>.+)$')
    def put_in(event):
        target = event.actor.Positioned.pick_nearby_inventory(event.target_descriptor)
        if not target:
            return

        container = event.actor.Positioned.pick_nearby_inventory(event.container_descriptor)
        if not container:
            return

        if not container.Positioned.is_container:
            event.actor.tell("{0.Name} can't hold items.".format(container))
            return

        event.trigger('before')
        if event.prevented:
            return

        event.actor.tell('You put {0.name} in {1.name}.'.format(target, container))
        event.actor.Positioned.emit('{0.Name} puts {1.name} in {2.name}.'.format(event.actor, target, container), exclude=(target, container))
        container.tell('{0.Name} puts {1.name} in your inventory.'.format(event.actor, target))
        target.tell('{0.Name} puts you in {1.name}.'.format(event.actor, container))
        container.Positioned.store(target)

    @action(r'^drop (?P<descriptor>.+)$')
    def drop(event):
        event.target = target = event.actor.Positioned.pick_inventory(event.descriptor)
        if not target:
            return

        event.trigger('before')

        event.actor.Positioned.remove(target)
        event.actor.tell('You drop {0.name}.'.format(target))
        event.actor.Positioned.emit('{0.Name} drops {1.name}.'.format(event.actor, target), exclude=target)
        target.tell('{0.Name} drops you.'.format(event.actor))

    @action('^(?:w(?:alk)?|go) (?P<direction>.+)$')
    def walk(event):
        # FIXME: assumes actor is Positioned
        # if not event.actor.has_aspect(Positioned): ...
        room = event.actor.Positioned.container

        exits = room.Positioned.exits()
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

        event.trigger('before')
        if event.prevented:
            return

        event.actor.tell('You travel {0}.'.format(event.direction))
        event.actor.Positioned.emit('{0.Name} travels {1} to {2.name}.'.format(event.actor, event.direction, destination))
        destination.Positioned.announce('{0.Name} arrives from {1.name}.'.format(event.actor, room))
        destination.Positioned.store(event.actor)

        event.actor.Positioned.tell_surroundings()

    @action(r'^enter (?P<descriptor>.+)$')
    def enter(event):
        # FIXME: assumes actor is Positioned
        # if not event.actor.has_aspect(Positioned): ...
        room = event.actor.Positioned.container

        container = event.actor.Positioned.pick_nearby(event.descriptor)
        if not container:
            return

        if not container.Positioned.is_container or not container.Positioned.is_enterable:
            event.actor.tell("You can't enter that.")
            return

        event.trigger('before')
        if event.prevented:
            return

        event.actor.tell('You enter {0.name}.'.format(container))
        event.actor.Positioned.emit('{0.Name} enters {1.name}.'.format(event.actor, container))
        container.Positioned.announce('{0.Name} arrives from {1.name}.'.format(event.actor, room))
        container.Positioned.store(event.actor)

        event.actor.Positioned.tell_surroundings()

    ##########################
    # Aliases and shortcuts
    ##########################

    @action('^(?:i|inv|inventory)$')
    def tell_inventory(event):
        return event.actor.perform('look in self')

    @action('^n$')
    def go_north(event):
        return event.actor.perform('go north')

    @action('^s$')
    def go_south(event):
        return event.actor.perform('go south')

    @action('^e$')
    def go_east(event):
        return event.actor.perform('go east')

    @action('^w$')
    def go_west(event):
        return event.actor.perform('go west')
