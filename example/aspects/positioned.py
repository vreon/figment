from schema import Aspect, action

class Positioned(Aspect):
    def __init__(self, is_container=False, is_carriable=False, is_enterable=False):
        self.container_id = None
        self.is_container = is_container
        self.is_carriable = is_carriable
        self.is_enterable = is_enterable

        self._contents = set()
        self._exits = {}

    def to_dict(self):
        return {
            'is_container': self.is_container,
            'container_id': self.container_id,
            'is_carriable': self.is_carriable,
            'is_enterable': self.is_enterable,
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

    def nearby(self):
        return set(entity for entity in self.container.contents() if not entity == self.entity)

    def pick(self, descriptor, entity_set):
        """
        Pick entities from a set by descriptor (name or ID). In most cases you
        should use one of the higher-level pick_* functions.
        """
        value = descriptor.value
        if value in ('self', 'me', 'myself'):
            return set((self.entity,))

        return set(e for e in entity_set if (value.lower() in e.name.lower() or value == e.id) and not e.is_invisible)

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
        return self.pick_interactively(descriptor, container.contents(), area='in {0.name}'.format(container))

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
            return Positioned.get(self.container_id)

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

        exits = room.exits()
        if exits:
            messages.append('Exits:')
            for direction, destination in exits.items():
                messages.append(indent('{0}: {1}'.format(direction, destination.name)))

        entities_nearby = [e for e in self.nearby() if not e.is_invisible]
        if entities_nearby:
            messages.append('Things nearby:')
            for entity in entities_nearby:
                messages.append(indent(entity.name))

        self.entity.tell('\n'.join(messages))

    ### TODO: Remove me

    def trigger(self, *args, **kwargs):
        pass

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
            event.actor.emit('{0.Name} says: "{1}"'.format(event.actor, message))

    # @action(r'^l(?:ook)?(?: around)?$')
    # def look(event):
    #     if self.trigger('before_look'):
    #         return

    #     self.emit('{0.Name} looks around.'.format(self.entity))
    #     self.tell_surroundings()

    #     self.trigger('after_look')

    # @action(r'^l(?:ook)? (?:in(?:to|side(?: of)?)?) (.+)$')
    # def look_in(self, descriptor):
    #     target = self.pick_nearby_inventory(descriptor)
    #     if not target:
    #         return

    #     if not target.Positioned.is_container:
    #         self.entity.tell("You can't look inside of that.")
    #         return

    #     if self.trigger('before_look_in', target):
    #         return

    #     self.entity.tell('Contents:')

    #     contents = [e for e in target.contents() if not e.is_invisible]
    #     if contents:
    #         for item in contents:
    #             self.entity.tell(indent('{0.name}'.format(item)))
    #     else:
    #         self.entity.tell(indent('nothing'))

    #     self.trigger('after_look_in', target)

    # @action(r'^(?:ex(?:amine)?|l(?:ook)?) (?:at )?(.+)$')
    # def look_at(self, descriptor):
    #     target = self.pick_nearby_inventory(descriptor)
    #     if not target:
    #         return

    #     if self.trigger('before_look_at', target):
    #         return

    #     self.entity.tell(target.desc)
    #     self.emit('{0.Name} looks at {1}.'.format(self.entity, target.name), exclude=target)
    #     target.tell('{0.Name} looks at you.'.format(self.entity))

    #     self.trigger('after_look_at', target)

    # @action('^(?:get|take) (.+)$')
    # def get(self, descriptor):
    #     if not self.is_container:
    #         self.entity.tell("You're unable to hold items.")
    #         return

    #     item = self.pick_nearby(descriptor)
    #     if not item:
    #         return

    #     if item == self.entity:
    #         self.entity.tell("You can't put yourself in your inventory.")
    #         return

    #     if not item.Positioned.is_carriable:
    #         self.entity.tell("That can't be carried.")
    #         return

    #     if self.trigger('before_get', item):
    #         return

    #     self.entity.tell('You pick up {0.name}.'.format(item))
    #     self.emit('{0.Name} picks up {1.name}.'.format(self.entity, item), exclude=item)
    #     item.tell('{0.Name} picks you up.'.format(self.entity))
    #     self.store(item)

    #     self.trigger('after_get', item)

    # @action('^(?:get|take) (.+) from (.+)$')
    # def get_from(self, target_descriptor, container_descriptor):
    #     if not self.is_container:
    #         self.entity.tell("You're unable to hold items.")
    #         return

    #     container = self.pick_nearby_inventory(container_descriptor)
    #     if not container:
    #         return

    #     if container == self.entity:
    #         self.entity.tell("You can't get things from your inventory, they'd just go right back in!")
    #         return

    #     if not container.Positioned.is_container:
    #         self.entity.tell("{0.Name} can't hold items.".format(container))
    #         return

    #     item = self.pick_from(target_descriptor, container)
    #     if not item:
    #         return

    #     if item == self.entity:
    #         self.entity.tell("You can't put yourself in your inventory.")
    #         return

    #     if self.trigger('before_get_from', item, container):
    #         return

    #     self.entity.tell('You take {0.name} from {1.name}.'.format(item, container))
    #     self.emit('{0.Name} takes {1.name} from {2.name}.'.format(self.entity, item, container), exclude=(item, container))
    #     container.tell('{0.Name} takes {1.name} from you.'.format(self.entity, item))
    #     item.tell('{0.Name} takes you from {1.name}.'.format(self.entity, container))
    #     self.store(item)

    #     self.trigger('after_get_from', item, container)

    # @action(r'^put (.+) in (.+)$')
    # def put_in(self, target_descriptor, container_descriptor):
    #     item = self.pick_nearby_inventory(target_descriptor)
    #     if not item:
    #         return

    #     container = self.pick_nearby_inventory(container_descriptor)
    #     if not container:
    #         return

    #     if not container.Positioned.is_container:
    #         self.entity.tell("{0.Name} can't hold items.".format(container))
    #         return

    #     if self.trigger('before_put_in', item, container):
    #         return

    #     self.entity.tell('You put {0.name} in {1.name}.'.format(item, container))
    #     self.emit('{0.Name} puts {1.name} in {2.name}.'.format(self.entity, item, container), exclude=(item, container))
    #     container.tell('{0.Name} puts {1.name} in your inventory.'.format(self.entity, item))
    #     item.tell('{0.Name} puts you in {1.name}.'.format(self.entity, container))
    #     container.store(item)

    #     self.trigger('after_put_in', item, container)

    # @action(r'^drop (.+)$')
    # def drop(self, descriptor):
    #     item = self.pick_inventory(descriptor)
    #     if not item:
    #         return

    #     if self.trigger('before_drop', item):
    #         return

    #     self.remove(item)
    #     self.entity.tell('You drop {0.name}.'.format(item))
    #     self.emit('{0.Name} drops {1.name}.'.format(self.entity, item), exclude=item)
    #     item.tell('{0.Name} drops you.'.format(self.entity))

    #     self.trigger('after_drop', item)

    # @action('^(?:w(?:alk)?|go) (.+)$')
    # def walk(self, direction):
    #     room = self.container

    #     exits = room.exits()
    #     if not exits:
    #         self.entity.tell("There don't seem to be any exits here.")
    #         return

    #     direction = direction.value
    #     for exit in exits:
    #         if direction.lower() == exit.lower():
    #             direction = exit
    #             break
    #     else:
    #         self.entity.tell("You're unable to go that way.")
    #         return

    #     destination = exits[direction]

    #     if self.trigger('before_walk', direction, destination):
    #         return

    #     self.entity.tell('You travel {0}.'.format(direction))
    #     self.emit('{0.Name} travels {1} to {2.name}.'.format(self.entity, direction, destination))
    #     destination.announce('{0.Name} arrives from {1.name}.'.format(self.entity, self.container))
    #     destination.store(self.entity)

    #     self.tell_surroundings()

    #     # self.trigger('after_walk', direction, source)

    # @action(r'^enter (.+)$')
    # def enter(self, descriptor):
    #     room = self.container

    #     container = self.pick_nearby(descriptor)
    #     if not container:
    #         return

    #     if not container.Positioned.is_container or not container.Positioned.is_enterable:
    #         self.entity.tell("You can't enter that.")
    #         return

    #     # for ent in [self.container, container] + self.nearby():
    #         # if not ent.trigger('before_enter', (self.entity, container)):
    #             # return

    #     self.entity.tell('You enter {0.name}.'.format(container))
    #     self.emit('{0.Name} enters {1.name}.'.format(self.entity, container))
    #     container.announce('{0.Name} arrives from {1.name}.'.format(self.entity, self.container))
    #     container.store(self.entity)

    #     self.tell_surroundings()

    #     # for ent in [container] + self.nearby():
    #         # ent.trigger('after_enter', (self, container))

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
