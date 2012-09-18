import random
import string
import json
from redis import StrictRedis
from juggernaut import Juggernaut
from schema.utils import upper_first, str_to_bool, indent
import tempfile
import shutil
import os

redis = StrictRedis()
jug = Juggernaut()


# TODO: Move these to utils
def _to_id(entity_or_id):
    if isinstance(entity_or_id, Entity):
        return entity_or_id.id
    return entity_or_id


def _to_entity(entity_or_id):
    if isinstance(entity_or_id, Entity):
        return entity_or_id
    return Entity.get(entity_or_id)


class AmbiguousDescriptor(Exception):
    pass


ACTIONS = {}


def action(pattern):
    def decorator(f):
        def wrapper(self, *args):
            try:
                return f(self, *[CommandArgument(i, v) for i, v in enumerate(args)])
            except AmbiguousDescriptor as ex:
                descriptor, targets = ex.args
                self.mode = DisambiguateMode(
                    self, self.mode, targets, f.__name__, args, descriptor.index
                )
        ACTIONS[pattern] = wrapper
        return wrapper
    return decorator


class CommandArgument(object):
    """
    An 'intelligent parameter' that knows its position in the player
    command. This is so ambiguities can be resolved later.
    """
    def __init__(self, index, value):
        self.index = index
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return 'CommandArgument(%r, %r)' % (self.index, self.value)


class Entity(object):
    ALL = {}
    START_ROOM = None

    def __init__(self, name, desc, **kwargs):
        self.id = Entity.create_id() if not 'id' in kwargs else kwargs['id']
        self.name = name
        self.desc = desc
        self.mode = ExploreMode(self)
        self.container_id = None
        self.is_container = False
        self.is_invisible = False
        self.is_carriable = False
        self.is_enterable = False
        self.is_edible = False
        self.is_potable = False

        self._contents = set()
        self._exits = {}
        self._behaviors = []

        # TODO: This is kind of a hack
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

        Entity.ALL[self.id] = self

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.id == other.id
        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        return NotImplemented if equal is NotImplemented else not equal

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def get(cls, id):
        return cls.ALL.get(id)

    @staticmethod
    def create_id():
        return ''.join(random.choice(string.ascii_letters) for i in xrange(12))

    @classmethod
    def all(cls):
        return cls.ALL.values()

    @property
    def messages_key(self):
        return 'entity:%s:messages' % self.id

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'mode': self.mode.to_dict(),
            'container_id': self.container_id,
            'is_container': self.is_container,
            'is_invisible': self.is_invisible,
            'is_carriable': self.is_carriable,
            'is_enterable': self.is_enterable,
            'is_edible': self.is_edible,
            'is_potable': self.is_potable,
            'contents': list(self._contents),
            'exits': self._exits,
            'behaviors': '',  # TODO
        }

    @classmethod
    def from_dict(cls, dict_):
        entity = cls(dict_['name'], dict_['desc'], id=dict_['id'])
        entity.mode = _mode_from_dict(entity, dict_['mode'])

        entity.container_id = dict_['container_id']
        entity.is_container = dict_['is_container']
        entity.is_invisible = dict_['is_invisible']
        entity.is_carriable = dict_['is_carriable']
        entity.is_enterable = dict_['is_enterable']
        entity.is_edible = dict_['is_edible']
        entity.is_potable = dict_['is_potable']

        entity._contents = set(dict_['contents'])
        entity._exits = dict_['exits']
        # TODO: entity.behaviors

        cls.ALL[dict_['id']] = entity

        return entity

    @classmethod
    def dump(cls):
        child_pid = os.fork()

        if not child_pid:
            f = tempfile.NamedTemporaryFile(delete=False)
            f.write(json.dumps([e.to_dict() for e in cls.all()]))
            f.close()
            shutil.move(f.name, 'dump.json')
            os._exit(os.EX_OK)

    def destroy(self):
        for item in self.contents():
            item.container_id = self.container_id

        container = self.container
        if container:
            self.container._contents.remove(self.id)

        self._behaviors = []
        self._contents = set()
        self._exits = {}

        self.ALL.pop(self.id, None)

    def clone(self):
        clone = Entity(self.name, self.desc)

        # TODO: Copy properties
        # TODO: Copy behaviors
        # TODO: Copy exits
        # TODO: Clone (not copy) contents
        # TODO: Add clone to clone.container_id's contents

        return clone

    # Sacrificing Pythonic coding style here for convenience.
    @property
    def Name(self):
        return upper_first(self.name)

    def perform(self, command):
        command = ' '.join(command.strip().split())
        self.mode.perform(command)

    def nearby(self):
        return set(entity for entity in self.container.contents() if not entity == self)

    def pick(self, descriptor, entity_set):
        """
        Pick entities from a set by descriptor (name or ID). In most cases you
        should use one of the higher-level pick_* functions.
        """
        value = descriptor.value
        if value in ('self', 'me', 'myself'):
            return set((self,))

        return set(e for e in entity_set if (value.lower() in e.name.lower() or value == e.id) and not e.is_invisible)

    def pick_interactively(self, descriptor, entity_set, area='in that area'):
        """
        Possibly target an object, and possibly enter interactive
        disambiguation mode.  `command` should be an action string with ? as a
        substitute for the eventual entity ID.
        """
        entities = self.pick(descriptor, entity_set)
        matches = len(entities)

        if matches == 0:
            self.tell("There's no {0} {1}.".format(descriptor, area))
        elif matches == 1:
            return entities.pop()
        else:
            self.tell("Which '{0}' do you mean?".format(descriptor.value))
            targets = []
            for index, entity in enumerate(entities):
                position = 'in inventory' if entity.container == self else 'nearby'
                self.tell(indent('{0}. {1.name} ({2})'.format(index + 1, entity, position)))
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
        old_container = entity.container

        if old_container:
            old_container._contents.remove(entity.id)

        container._contents.add(entity.id)
        entity.container_id = container.id

    def store(self, entity):
        Entity.move(entity, self)

    # TODO: Rename to drop (but collides with action of same name)
    def remove(self, entity):
        Entity.move(entity, self.container)

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
                id = self.id
            elif descriptor == '..':
                id = self.container_id
            else:
                id = descriptor
            resolved_exits[name] = Entity.get(id)
        return resolved_exits

    def link(self, direction, destination, back_direction=None):
        # NOTE: This depends on _to_id not transforming values like . or ..
        destination_id = _to_id(destination)
        self._exits[direction] = destination_id
        if back_direction and not destination in ('.', '..'):
            destination = _to_entity(destination)
            destination._exits[back_direction] = self.id

    #########################
    # Communication
    #########################

    def tell(self, message):
        """Send text to this entity."""
        jug.publish(self.messages_key, message)

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
        exclude.add(self)
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

        self.tell('\n'.join(messages))

    #########################
    # Events and behaviors
    #########################

    # TODO
    def trigger(self, event, *args):
        # listeners = self.nearby() | self.contents()
        # listeners.add(self)

        # container = self.container
        # if container:
        #     listeners.add(container)

        # args = list(args)
        # args.insert(0, self) # Every behavior gets the actor as the first argument

        # any_overridden = False
        # for listener in listeners:
        #     if listener.respond_to(event, *args, **kwargs):
        #         any_overridden = True

        # return any_overridden
        return False

    def respond_to(self, event, *args):
        # TODO: Every action should be a behavior
        # This true/false stuff can be replaced with calls to super() (the default behavior)
        # Instead of flag properties, add Behaviors; Edible, Invisible ... might need to think about this more
        # entity_behaviors = redis.hgetall(self.behaviors_key)
        # for behavior_instance in self._behaviors.values():
        #     getattr(behavior_instance, event, None)(*args)
        return False

    #########################
    # Actions
    #########################

    @action(r'^dump$')
    def do_dump(self):
        self.tell('Dumping!')
        Entity.dump()

    @action(r'^name$')
    def get_name(self):
        self.tell('Your name is {0.name}.'.format(self))

    @action(r'^name (.+)$')
    def set_name(self, descriptor):
        name = upper_first(descriptor.value) # TODO: name filtering :p
        for entity in self.nearby():
            entity.tell('{0.Name} is now known as {1}.'.format(self, name))
        self.tell('Your name is now {0}.'.format(name))
        self.name = name

    @action(r'^divine (.+)$')
    def divine(self, descriptor):
        target = self.pick_nearby_inventory(descriptor)
        self.tell('You suddenly know more than you needed to about {0.name}.'.format(target))
        for key in [
            'id', 'name', 'desc', 'container_id', 'is_container',
            'is_carriable', 'is_enterable', 'is_edible', 'is_potable',
            'is_invisible',
        ]:
            self.tell(indent(('%s: {.%s}' % (key, key)).format(target)))

    @action(r'^s(?:ay)? (.+)$')
    def say(self, message):
        message = upper_first(message.value.strip().replace('"', "'"))

        if not message[-1] in ('.', '?', '!'):
            message += '.'

        if self.trigger('before_say', message):
            return

        self.tell('You say: "{0}"'.format(message))
        self.emit('{0.Name} says: "{1}"'.format(self, message))

        self.trigger('after_say', message)

    @action(r'^l(?:ook)?(?: around)?$')
    def look(self):
        if self.trigger('before_look'):
            return

        self.emit('{0.Name} looks around.'.format(self))
        self.tell_surroundings()

        self.trigger('after_look')

    @action(r'^l(?:ook)? (?:in(?:to|side(?: of)?)?) (.+)$')
    def look_in(self, descriptor):
        target = self.pick_nearby_inventory(descriptor)
        if not target:
            return

        if not target.is_container:
            self.tell("You can't look inside of that.")
            return

        if self.trigger('before_look_in', target):
            return

        self.tell('Contents:')

        contents = [e for e in target.contents() if not e.is_invisible]
        if contents:
            for item in contents:
                self.tell(indent('{0.name}'.format(item)))
        else:
            self.tell(indent('nothing'))

        self.trigger('after_look_in', target)

    @action(r'^(?:ex(?:amine)?|l(?:ook)?) (?:at )?(.+)$')
    def look_at(self, descriptor):
        target = self.pick_nearby_inventory(descriptor)
        if not target:
            return

        if self.trigger('before_look_at', target):
            return

        self.tell(target.desc)
        self.emit('{0.Name} looks at {1}.'.format(self, target.name), exclude=target)
        target.tell('{0.Name} looks at you.'.format(self))

        self.trigger('after_look_at', target)

    @action(r'^use (.+)$')
    def use(self, target_descriptor):
        item = self.pick_nearby_inventory(target_descriptor)
        if not item:
            return

        if self.trigger('before_use', item):
            return

        self.tell('Nothing happens.')

    @action(r'^use (.+) on (.+)')
    def use_on(self, item_descriptor, target_descriptor):
        item = self.pick_nearby_inventory(item_descriptor)
        if not item:
            return

        target = self.pick_nearby_inventory(target_descriptor)
        if not target:
            return

        if self.trigger('before_use_on', item, target):
            return

        self.tell('Nothing happens.')

    @action('^(?:get|take) (.+)$')
    def _get(self, descriptor):
        if not self.is_container:
            self.tell("You're unable to hold items.")
            return

        item = self.pick_nearby(descriptor)
        if not item:
            return

        if item == self:
            self.tell("You can't put yourself in your inventory.")
            return

        if not item.is_carriable:
            self.tell("That can't be carried.")
            return

        if self.trigger('before_get', item):
            return

        self.tell('You pick up {0.name}.'.format(item))
        self.emit('{0.Name} picks up {1.name}.'.format(self, item), exclude=item)
        item.tell('{0.Name} picks you up.'.format(self))
        self.store(item)

        self.trigger('after_get', item)

    @action('^(?:get|take) (.+) from (.+)$')
    def get_from(self, target_descriptor, container_descriptor):
        if not self.is_container:
            self.tell("You're unable to hold items.")
            return

        container = self.pick_nearby_inventory(container_descriptor)
        if not container:
            return

        if container == self:
            self.tell("You can't get things from your inventory, they'd just go right back in!")
            return

        if not container.is_container:
            self.tell("{0.Name} can't hold items.".format(container))
            return

        item = self.pick_from(target_descriptor, container)
        if not item:
            return

        if item == self:
            self.tell("You can't put yourself in your inventory.")
            return

        if self.trigger('before_get_from', item, container):
            return

        self.tell('You take {0.name} from {1.name}.'.format(item, container))
        self.emit('{0.Name} takes {1.name} from {2.name}.'.format(self, item, container), exclude=(item, container))
        container.tell('{0.Name} takes {1.name} from you.'.format(self, item))
        item.tell('{0.Name} takes you from {1.name}.'.format(self, container))
        self.store(item)

        self.trigger('after_get_from', item, container)

    @action(r'^put (.+) in (.+)$')
    def put_in(self, target_descriptor, container_descriptor):
        item = self.pick_nearby_inventory(target_descriptor)
        if not item:
            return

        container = self.pick_nearby_inventory(container_descriptor)
        if not container:
            return

        if not container.is_container:
            self.tell("{0.Name} can't hold items.".format(container))
            return

        if self.trigger('before_put_in', item, container):
            return

        self.tell('You put {0.name} in {1.name}.'.format(item, container))
        self.emit('{0.Name} puts {1.name} in {2.name}.'.format(self, item, container), exclude=(item, container))
        container.tell('{0.Name} puts {1.name} in your inventory.'.format(self, item))
        item.tell('{0.Name} puts you in {1.name}.'.format(self, container))
        container.store(item)

        self.trigger('after_put_in', item, container)

    @action(r'^drop (.+)$')
    def drop(self, descriptor):
        item = self.pick_inventory(descriptor)
        if not item:
            return

        if self.trigger('before_drop', item):
            return

        self.remove(item)
        self.tell('You drop {0.name}.'.format(item))
        self.emit('{0.Name} drops {1.name}.'.format(self, item), exclude=item)
        item.tell('{0.Name} drops you.'.format(self))

        self.trigger('after_drop', item)

    @action(r'^drink (.+)$')
    def drink(self, descriptor):
        item = self.pick_nearby_inventory(descriptor)
        if not item:
            return

        if not item.is_potable:
            self.tell("You can't drink that.")
            if item.is_edible:
                self.tell('You may be able to eat it, though.')
            return

        # TODO: events

        self.tell('You drink {0.name}.'.format(item))
        self.emit('{0.Name} drinks {1.name}.'.format(self, item), exclude=item)
        item.tell('{0.Name} drinks you.'.format(self))
        item.destroy()

        # TODO: events

    @action(r'^eat (.+)$')
    def eat(self, descriptor):
        item = self.pick_nearby_inventory(descriptor)
        if not item:
            return

        if not item.is_edible:
            self.tell("You can't eat that.")
            if item.is_potable:
                self.tell('You may be able to drink it, though.')
            return

        # TODO: events

        self.tell('You eat {0.name}.'.format(item))
        self.emit('{0.Name} eats {1.name}.'.format(self, item), exclude=item)
        item.tell('{0.Name} eats you.'.format(self))
        item.destroy()

        # TODO: events

    @action('^(?:w(?:alk)?|go) (.+)$')
    def walk(self, direction):
        room = self.container

        exits = room.exits()
        if not exits:
            self.tell("There don't seem to be any exits here.")
            return

        direction = direction.value
        for exit in exits:
            if direction.lower() == exit.lower():
                direction = exit
                break
        else:
            self.tell("You're unable to go that way.")
            return

        destination = exits[direction]

        if self.trigger('before_walk', direction, destination):
            return

        self.tell('You travel {0}.'.format(direction))
        self.emit('{0.Name} travels {1} to {2.name}.'.format(self, direction, destination))
        destination.announce('{0.Name} arrives from {1.name}.'.format(self, self.container))
        destination.store(self)

        self.tell_surroundings()

        # self.trigger('after_walk', direction, source)

    @action(r'^enter (.+)$')
    def enter(self, descriptor):
        room = self.container

        container = self.pick_nearby(descriptor)
        if not container:
            return

        if not container.is_container or not container.is_enterable:
            self.tell("You can't enter that.")
            return

        # for ent in [self.container, container] + self.nearby():
            # if not ent.trigger('before_enter', (self, container)):
                # return

        self.tell('You enter {0.name}.'.format(container))
        self.emit('{0.Name} enters {1.name}.'.format(self, container))
        container.announce('{0.Name} arrives from {1.name}.'.format(self, self.container))
        container.store(self)

        self.tell_surroundings()

        # for ent in [container] + self.nearby():
            # ent.trigger('after_enter', (self, container))

    @action(r'^help$')
    def help(self):
        cmds = (
            'enter drink eat name say look get put drop dance laugh blink '
            'frown eyebrow shrug smile grin bow nod cheer cough cry point '
            'help inventory walk go travel wave l inv take s lol wink'
        ).split()
        cmds.sort()

        self.tell('Known commands:')

        line = []
        for cmd in cmds:
            line.append(cmd.rjust(11))
            if len(line) == 7:
                self.tell(''.join(line))
                line = []
        if line:
            self.tell(''.join(line))

    ##########################
    # Emotes
    ##########################

    def emote(self, descriptor, verb, plural=None, join='at'):
        if not plural:
            plural = verb + 's'

        if not descriptor.value:
            self.emit('{0.Name} {1}.'.format(self, plural))
            self.tell('You {0}.'.format(verb))
            return

        target = self.pick_nearby(descriptor)
        if not target:
            return

        self.emit('{0.Name} {1} {2} {3.name}.'.format(self, plural, join, target), exclude=target)
        self.tell('You {0} {1} {2.name}.'.format(verb, join, target))
        target.tell('{0.Name} {1} {2} you.'.format(self, plural, join))

    @action(r'^dance(?: with (.+))?$')
    def dance(self, descriptor):
        self.emote(descriptor, 'dance', join='with')

    @action(r'^laugh(?: at (.+))?$')
    def laugh(self, descriptor):
        self.emote(descriptor, 'laugh')

    @action(r'^lol$')
    def lol(self):
        self.laugh(None)

    @action(r'^blink(?: at (.+))?$')
    def blink(self, descriptor):
        self.emote(descriptor, 'blink')

    @action(r'^frown(?: at (.+))?$')
    def frown(self, descriptor):
        self.emote(descriptor, 'frown')

    @action(r'^eyebrow(?: at (.+))?$')
    def eyebrow(self, descriptor):
        self.emote(descriptor, 'raise an eyebrow', 'raises an eyebrow')

    @action(r'^shrug(?: at (.+))?$')
    def shrug(self, descriptor):
        self.emote(descriptor, 'shrug')

    @action(r'^smile(?: at (.+))?$')
    def smile(self, descriptor):
        self.emote(descriptor, 'smile')

    @action(r'^grin(?: at (.+))?$')
    def grin(self, descriptor):
        self.emote(descriptor, 'grin')

    @action(r'^bow(?: to (.+))?$')
    def bow(self, descriptor):
        self.emote(descriptor, 'bow', join='to')

    @action(r'^nod(?: (at|to) (.+))?$')
    def nod(self, join, descriptor):
        self.emote(descriptor, 'nod', join=join.value)

    @action(r'^cheer(?: for (.+))?$')
    def cheer(self, descriptor):
        self.emote(descriptor, 'cheer', join='for')

    @action(r'^cough(?: (on|at) (.+))?$')
    def cough(self, join, descriptor):
        self.emote(descriptor, 'cough', join=join.value)

    @action(r'^cry(?: on (.+))?$')
    def cry(self, descriptor):
        self.emote(descriptor, 'cry', 'cries', join='on')

    @action(r'^point(?: (to|at) (.+))?$')
    def point(self, join, descriptor):
        self.emote(descriptor, 'point', join=join.value)

    @action(r'^wave(?: (to|at) (.+))?$')
    def wave(self, join, descriptor):
        self.emote(descriptor, 'wave', join=join.value)

    @action(r'^wink(?: (to|at) (.+))?$')
    def wink(self, join, descriptor):
        self.emote(descriptor, 'wink', join=join.value)

    ##########################
    # Aliases and shortcuts
    ##########################

    @action('^(?:i|inv|inventory)$')
    def tell_inventory(self):
        return self.perform('look in self')

    @action('^n$')
    def go_north(self):
        return self.perform('go north')

    @action('^s$')
    def go_south(self):
        return self.perform('go south')

    @action('^e$')
    def go_east(self):
        return self.perform('go east')

    @action('^w$')
    def go_west(self):
        return self.perform('go west')

def create_player():
    player = Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        is_container = True,
    )
    player.link('out', '..')
    Entity.get(Entity.START_ROOM).store(player)
    player.emit('A new player appears.')

    hubstone = Entity(
        'a hubstone',
        'A fragment of an ancient artifact with space-bending abilities.',
        is_carriable = True,
    )
    # hubstone.add_behavior('hubstone')
    player.store(hubstone)

    return player


def create_world():
    redis.flushdb()

    room = Entity(
        'Example Room',
        'This room is for demonstration purposes only.',
        is_container = True,
    )
    Entity.START_ROOM = room.id

    for letter in 'ABCDE':
        thingy = Entity(
            'Thingy ' + letter,
            "It's a thingy emblazoned with the letter " + letter + '.',
            is_carriable = True,
        )
        room.store(thingy)

    box = Entity(
        'a box',
        "It's a box made of cardboard. Nothing to get excited about.",
        is_container = True,
        is_enterable = True,
    )
    box.link('out', '..')
    room.store(box)

    backpack = Entity(
        'a backpack',
        "A plain green backpack.",
        is_container = True,
        is_carriable = True,
    )
    room.store(backpack)

    other_room = Entity(
        'The Other Room',
        "It's another room.",
        is_container = True,
    )
    room.link('north', other_room, 'south')

    blob = Entity(
        'a sticky blob',
        "This blob looks difficult to drop.",
        is_carriable = True,
    )
    # blob.add_behavior('stickyblob')
    other_room.store(blob)

    gen = Entity(
        'a subspace generator',
        "A very complex-looking device with a button on one side.",
        is_carriable = True,
    )
    # gen.add_behavior('roomcreator')
    other_room.store(gen)


# from schema.behaviors import BEHAVIORS
from schema.modes import ExploreMode, DisambiguateMode, _mode_from_dict
