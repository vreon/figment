import string
from figment import Component, Entity
from figment.utils import upper_first, indent
from modes import ActionMode

def to_id(entity_or_id):
    if isinstance(entity_or_id, Entity):
        return entity_or_id.id
    return entity_or_id


def to_entity(entity_or_id):
    if isinstance(entity_or_id, Entity):
        return entity_or_id
    return Entity.get(entity_or_id)


class Spatial(Component):
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
        super(Spatial, self).attach(entity)

        container = self.container
        if container:
            container.Spatial._contents.add(self.entity.id)

    def detach(self):
        for item in self.contents():
            item.Spatial.container_id = self.container_id

        container = self.container
        if container:
            container.Spatial._contents.remove(self.entity.id)

        self._contents = set()
        self._exits = {}

        super(Spatial, self).detach()

    #########################
    # Selection
    #########################

    def nearby(self):
        return set(entity for entity in self.container.Spatial.contents() if not entity == self.entity)

    def pick(self, selector, entity_set):
        """
        Pick entities from a set by selector (name or ID). In most cases you
        should use one of the higher-level pick_* functions.
        """
        if selector.lower() in ('self', 'me', 'myself'):
            return set((self.entity,))

        return set(e for e in entity_set if (selector.lower() in e.name.lower() or selector == e.id) and e.Spatial.is_visible)

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
                location = 'in inventory' if entity.Spatial.container == self.entity else 'nearby'
                self.entity.tell(indent('{0}. {1.name} ({2})'.format(index + 1, entity, location)))
                targets.append(entity.id)
            # raise AmbiguousSelector(selector, targets)

    def pick_nearby(self, selector):
        return self.pick_interactively(selector, self.nearby(), area='nearby')

    def pick_inventory(self, selector):
        return self.pick_interactively(selector, self.contents(), area='in your inventory')

    def pick_from(self, selector, container):
        return self.pick_interactively(selector, container.Spatial.contents(), area='in {0.name}'.format(container))

    def pick_nearby_inventory(self, selector):
        return self.pick_interactively(selector, self.contents() | self.nearby(), area='nearby')

    #########################
    # Location, contents
    #########################

    @staticmethod
    def move(entity, container):
        old_container = entity.Spatial.container

        if old_container:
            old_container.Spatial._contents.remove(entity.id)

        container.Spatial._contents.add(entity.id)
        entity.Spatial.container_id = container.id

    def store(self, entity):
        Spatial.move(entity, self.entity)

    def store_in(self, entity):
        Spatial.move(self.entity, entity)

    def unstore(self, entity):
        Spatial.move(entity, self.container)

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
            destination.Spatial._exits[back_direction] = self.entity.id

    def unlink(self, direction, destination, back_direction=None):
        # NOTE: This depends on _to_id not transforming values like . or ..
        destination_id = to_id(destination)
        self._exits.pop(direction, None)
        if back_direction and not destination in ('.', '..'):
            destination = to_entity(destination)
            destination.Spatial._exits.pop(back_direction, None)

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

        exits = room.Spatial.exits()
        if exits:
            messages.append('Exits:')
            for direction, destination in exits.items():
                messages.append(indent('{0}: {1}'.format(direction, destination.name)))

        entities_nearby = [e for e in self.nearby() if e.Spatial.is_visible]
        if entities_nearby:
            messages.append('Things nearby:')
            for entity in entities_nearby:
                messages.append(indent(entity.name))

        self.entity.tell('\n'.join(messages))


#########################
# Actions
#########################

@ActionMode.action(r'^s(?:ay)? (?P<message>.+)$')
def say(actor, message):
    if not actor.is_(Spatial):
        actor.tell("You're unable to do that.")
        return

    message = upper_first(message.strip().replace('"', "'"))

    if not message[-1] in ('.', '?', '!'):
        message += '.'

    for witness in actor.Spatial.nearby():
        if witness.is_([Spatial, 'Psychic']):
            witness.perform(Spatial.say, message=message)

    actor.tell('You say: "{0}"'.format(message))
    actor.Spatial.emit('{0.Name} says: "{1}"'.format(actor, message))


@ActionMode.action(r'^l(?:ook)?(?: around)?$')
def look(actor):
    if not actor.is_(Spatial):
        actor.tell("You're unable to do that.")
        return

    if actor.Spatial.container.is_('Dark'):
        actor.tell("It's too dark to see anything here.")
        return

    actor.Spatial.emit('{0.Name} looks around.'.format(actor))
    actor.Spatial.tell_surroundings()


@ActionMode.action(r'^l(?:ook)? (?:in(?:to|side(?: of)?)?) (?P<selector>.+)$')
def look_in(actor, selector):
    if not actor.is_(Spatial):
        actor.tell("You're unable to do that.")
        return

    target = actor.Spatial.pick_nearby_inventory(selector)
    if not target:
        return

    if not target.is_(Spatial) or not target.Spatial.is_container:
        actor.tell("You can't look inside of that.")
        return

    if target.is_('Dark'):
        actor.tell("It's too dark in there to see anything.")
        return

    actor.tell('Contents:')

    contents = [e for e in target.Spatial.contents() if e.Spatial.is_visible]
    if contents:
        for item in contents:
            actor.tell(indent('{0.name}'.format(item)))
    else:
        actor.tell(indent('nothing'))


@ActionMode.action(r'^(?:ex(?:amine)?|l(?:ook)?) (?:at )?(?P<selector>.+)$')
def look_at(actor, selector):
    if not actor.is_(Spatial):
        actor.tell("You're unable to do that.")
        return

    if actor.Spatial.container.is_('Dark'):
        actor.tell("It's too dark to see anything here.")
        return

    target = actor.Spatial.pick_nearby_inventory(selector)
    if not target:
        return

    actor.tell(target.desc)
    actor.Spatial.emit('{0.Name} looks at {1}.'.format(actor, target.name), exclude=target)
    target.tell('{0.Name} looks at you.'.format(actor))


@ActionMode.action('^(?:get|take|pick up) (?P<selector>.+)$')
def get(actor, selector):
    if not actor.is_(Spatial) or not actor.Spatial.is_container:
        actor.tell("You're unable to do that.")
        return

    target = actor.Spatial.pick_nearby(selector)
    if not target:
        return

    if target == actor:
        actor.tell("You can't put yourself in your inventory.")
        return

    if not target.is_(Spatial) or not target.Spatial.is_carriable:
        actor.tell("That can't be carried.")
        return

    if target.is_('Important'):
        actor.tell('{0.Name} resists your attempt to grab it.'.format(target))
        return

    actor.tell('You pick up {0.name}.'.format(target))
    actor.Spatial.emit('{0.Name} picks up {1.name}.'.format(actor, target), exclude=target)
    target.tell('{0.Name} picks you up.'.format(actor))
    actor.Spatial.store(target)


@ActionMode.action('^(?:get|take|pick up) (?P<target_selector>.+) from (?P<container_selector>.+)$')
def get_from(actor, target_selector, container_selector):
    if not actor.is_(Spatial) or not actor.Spatial.is_container:
        actor.tell("You're unable to hold items.")
        return

    container = actor.Spatial.pick_nearby_inventory(container_selector)
    if not container:
        return

    if container == actor:
        actor.tell("You can't get things from your inventory, they'd just go right back in!")
        return

    if not container.is_(Spatial) or not container.Spatial.is_container:
        actor.tell("{0.Name} can't hold items.".format(container))
        return

    target = actor.Spatial.pick_from(target_selector, container)
    if not target:
        return

    if target == actor:
        actor.tell("You can't put yourself in your inventory.")
        return

    if not target.is_(Spatial):
        actor.tell("You can't take {0.name} from {1.name}.".format(target, container))
        return

    if target.is_('Important'):
        actor.tell('{0.Name} resists your attempt to grab it.'.format(target))
        return

    actor.tell('You take {0.name} from {1.name}.'.format(target, container))
    actor.Spatial.emit('{0.Name} takes {1.name} from {2.name}.'.format(actor, target, container), exclude=(target, container))
    container.tell('{0.Name} takes {1.name} from you.'.format(actor, target))
    target.tell('{0.Name} takes you from {1.name}.'.format(actor, container))
    actor.Spatial.store(target)


@ActionMode.action(r'^put (?P<target_selector>.+) (?:in(?:to|side(?: of)?)?) (?P<container_selector>.+)$')
def put_in(actor, target_selector, container_selector):
    if not actor.is_(Spatial) or not actor.Spatial.is_container:
        actor.tell("You're unable to hold things.")
        return

    target = actor.Spatial.pick_nearby_inventory(target_selector)
    if not target:
        return

    if not target.is_(Spatial):
        actor.tell("You can't put {0.name} into anything.")
        return

    if target.is_('Important'):
        actor.tell("You shouldn't get rid of this; it's very important.")
        return

    container = actor.Spatial.pick_nearby_inventory(container_selector)
    if not container:
        return

    if not container.is_(Spatial) or not container.Spatial.is_container:
        actor.tell("{0.Name} can't hold things.".format(container))
        return

    actor.tell('You put {0.name} in {1.name}.'.format(target, container))
    actor.Spatial.emit('{0.Name} puts {1.name} in {2.name}.'.format(actor, target, container), exclude=(target, container))
    container.tell('{0.Name} puts {1.name} in your inventory.'.format(actor, target))
    target.tell('{0.Name} puts you in {1.name}.'.format(actor, container))
    container.Spatial.store(target)


@ActionMode.action(r'^drop (?P<selector>.+)$')
def drop(actor, selector):
    if not actor.is_(Spatial):
        actor.tell("You're unable to drop things.")
        return

    target = actor.Spatial.pick_inventory(selector)
    if not target:
        return

    # TODO: other nearby stuff

    if target.is_('Important'):
        actor.tell("You shouldn't get rid of this; it's very important.")
        return

    if target.is_('Sticky') and not target.Sticky.roll_for_drop():
        actor.tell('You try to drop {0.name}, but it sticks to your hand.'.format(target))
        return

    actor.Spatial.unstore(target)
    actor.tell('You drop {0.name}.'.format(target))
    actor.Spatial.emit('{0.Name} drops {1.name}.'.format(actor, target), exclude=target)
    target.tell('{0.Name} drops you.'.format(actor))


@ActionMode.action('^(?:w(?:alk)?|go) (?P<direction>.+)$')
def walk(actor, direction):
    if not actor.is_(Spatial):
        actor.tell("You're unable to move.")
        return

    room = actor.Spatial.container

    # Actor is hanging out at the top level, or room is in a bad state
    if not room or not room.is_(Spatial):
        actor.tell("You're unable to leave this place.")
        return

    exits = room.Spatial.exits()
    if not exits:
        actor.tell("There don't seem to be any exits here.")
        return

    for exit_name in exits:
        if direction.lower() == exit_name.lower():
            direction = exit_name
            break
    else:
        actor.tell("You're unable to go that way.")
        return

    destination = exits[direction]

    # Ensure the destination is still a container
    if not destination or not destination.is_(Spatial) or not destination.Spatial.is_container:
        actor.tell("You're unable to go that way.")
        return

    actor.tell('You travel {0}.'.format(direction))
    actor.Spatial.emit('{0.Name} travels {1} to {2.name}.'.format(actor, direction, destination))
    destination.Spatial.announce('{0.Name} arrives from {1.name}.'.format(actor, room))
    destination.Spatial.store(actor)

    actor.Spatial.tell_surroundings()


@ActionMode.action(r'^enter (?P<selector>.+)$')
def enter(actor, selector):
    if not actor.is_(Spatial):
        actor.tell("You're unable to move.")
        return

    room = actor.Spatial.container

    # Actor is hanging out at the top level, or room is in a bad state
    if not room or not room.is_(Spatial):
        actor.tell("You're unable to leave this place.")
        return

    container = actor.Spatial.pick_nearby(selector)
    if not container:
        return

    if not container.is_(Spatial) or not container.Spatial.is_container or not container.Spatial.is_enterable:
        actor.tell("You can't enter that.")
        return

    actor.tell('You enter {0.name}.'.format(container))
    actor.Spatial.emit('{0.Name} enters {1.name}.'.format(actor, container))
    container.Spatial.announce('{0.Name} arrives from {1.name}.'.format(actor, room))
    container.Spatial.store(actor)

    actor.Spatial.tell_surroundings()


##########################
# Aliases and shortcuts
##########################

@ActionMode.action('^(?:i|inv|inventory)$')
def tell_inventory(actor):
    return actor.perform('look in self')

@ActionMode.action('^n(?:orth)?$')
def go_north(actor):
    return actor.perform('go north')

@ActionMode.action('^s(?:outh)?$')
def go_south(actor):
    return actor.perform('go south')

@ActionMode.action('^e(?:ast)?$')
def go_east(actor):
    return actor.perform('go east')

@ActionMode.action('^w(?:est)?$')
def go_west(actor):
    return actor.perform('go west')

@ActionMode.action('^(?:ne|northeast)$')
def go_northeast(actor):
    return actor.perform('go northeast')

@ActionMode.action('^(?:nw|northwest)$')
def go_northwest(actor):
    return actor.perform('go northwest')

@ActionMode.action('^(?:se|southeast)$')
def go_southeast(actor):
    return actor.perform('go southeast')

@ActionMode.action('^(?:sw|southwest)$')
def go_southwest(actor):
    return actor.perform('go southwest')

@ActionMode.action('^u(?:p)?$')
def go_up(actor):
    return actor.perform('go up')

@ActionMode.action('^d(?:own)?$')
def go_down(actor):
    return actor.perform('go down')
