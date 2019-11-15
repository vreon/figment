import string

from figment import Component, Entity
from figment.utils import upper_first, indent

from theworldfoundry.modes import ActionMode, DisambiguationMode


class Invisible(Component):
    pass


class Enterable(Component):
    pass


class Carriable(Component):
    pass


class Stackable(Component):
    def __init__(self, key, quantity=1):
        self.key = key
        self.quantity = quantity

    def to_dict(self):
        return {"key": self.key, "quantity": self.quantity}

    @classmethod
    def from_dict(cls, dict_):
        return cls(key=dict_["key"], quantity=dict_["quantity"])

    def split_off(self, quantity):
        clone = self.entity.zone.clone(self.entity)
        clone.Spatial.container = None
        clone.Stackable.quantity = quantity
        self.quantity -= quantity

        if self.quantity == 0:
            # TODO: Is there a bug here? Probably
            # (I bet the container keeps a reference to this defunct entity)
            self.entity.zone.destroy(self.entity)

        return clone

    @classmethod
    def consolidate(cls, entities):
        total_quantity = sum([e.Stackable.quantity for e in entities])

        for e in entities[1:]:
            # TODO: Ahhh!! This should really be handled by destroy!
            # (See TODO about entity lifecycle hooks)
            e.Spatial.unstore()
            e.zone.destroy(e)

        entities[0].Stackable.quantity = total_quantity

        return entities[0]

    def refine(self, fuzzy_quantity):
        if fuzzy_quantity == "all":
            return self.quantity

        try:
            quantity = min(max(0, int(fuzzy_quantity)), self.quantity)
            if quantity == 0:
                raise ValueError
        except ValueError:
            return

        return quantity

    @classmethod
    def convert(cls, fuzzy_quantity):
        if fuzzy_quantity == "all":
            return

        quantity = int(fuzzy_quantity)

        return quantity


class Container(Component):
    def __init__(self):
        self.contents_ids = set()

    def to_dict(self):
        return {"contents_ids": list(self.contents_ids)}

    @classmethod
    def from_dict(cls, dict_):
        self = cls()
        self.contents_ids = set(dict_["contents_ids"])
        return self

    def attach(self, entity):
        super(Container, self).attach(entity)
        self.contents = set([entity.zone.get(id) for id in self.contents_ids])

    def detach(self):
        self.contents = set()
        super(Container, self).detach()

    @staticmethod
    def move(entity, container, quantity=None):
        if quantity is not None and entity.is_(Stackable):
            entity = entity.Stackable.split_off(quantity)

        entity.Spatial.unstore()
        container.Container.contents_ids.add(entity.id)
        container.Container.contents.add(entity)
        entity.Spatial.container_id = container.id
        entity.Spatial.container = container

        return entity

    def consolidate_contents(self):
        stackables_by_key = {}

        for entity in self.contents:
            if entity.is_(Stackable):
                stackables_by_key.setdefault(entity.Stackable.key, []).append(entity)

        for key, entities in stackables_by_key.items():
            if len(entities) > 1:
                Stackable.consolidate(entities)

    def store(self, entity, quantity=None):
        return Container.move(entity, self.entity, quantity=quantity)

    def drop(self, entity, quantity=None):
        return Container.move(entity, self.entity.Spatial.container, quantity=quantity)

    def announce(self, message):
        """Send text to this entity's contents."""
        for listener in self.contents:
            listener.tell(message)


class Exitable(Component):
    def __init__(self):
        self.exit_ids = set()
        self.exits = set()

    def to_dict(self):
        return {"exit_ids": list(self.exit_ids)}

    @classmethod
    def from_dict(cls, dict_):
        self = cls()
        self.exit_ids = set(dict_["exit_ids"])
        return self

    def attach(self, entity):
        super(Exitable, self).attach(entity)
        self.exits = set([entity.zone.get(id) for id in self.exit_ids])

    def detach(self):
        self.exits = set()
        super(Exitable, self).detach()


class Exit(Component):
    def __init__(self, direction, destination_id):
        self.direction = direction
        self.destination_id = destination_id
        self.destination = None

    def to_dict(self):
        return {"direction": self.direction, "destination_id": self.destination_id}

    @classmethod
    def from_dict(cls, dict_):
        return cls(direction=dict_["direction"], destination_id=dict_["destination_id"])

    def attach(self, entity):
        super(Exit, self).attach(entity)
        self.destination = entity.zone.get(self.destination_id)

    def detach(self):
        self.destination = None
        super(Exit, self).detach()


class Spatial(Component):
    def __init__(self, container_id=None):
        self.container_id = container_id
        self.container = None

    def to_dict(self):
        return {"container_id": self.container_id}

    @classmethod
    def from_dict(cls, dict_):
        return cls(container_id=dict_["container_id"])

    def attach(self, entity):
        super(Spatial, self).attach(entity)
        self.container = entity.zone.get(self.container_id)

    def detach(self):
        self.container = None
        super(Spatial, self).detach()

    def store_in(self, entity):
        Container.move(self.entity, entity)

    def unstore(self):
        container = self.container
        if container:
            container.Container.contents_ids.remove(self.entity.id)
            container.Container.contents.remove(self.entity)

        self.container = None
        self.container_id = None

    #########################
    # Selection
    #########################

    def nearby(self):
        return set(
            entity
            for entity in self.container.Container.contents
            if not entity == self.entity
        )

    def pick(self, selector, entity_set, min_quantity=None):
        """
        Pick entities from a set by selector. In most cases you should use one
        of the higher-level pick_* functions.
        """
        if isinstance(selector, int):
            for e in entity_set:
                if e.id == selector:
                    return set((e,))
        else:
            if selector.lower() in ("self", "me", "myself"):
                return set((self.entity,))

            return set(
                e
                for e in entity_set
                if (e.is_("Named") and selector.lower() in e.Named.name.lower())
                and not e.is_(Invisible)
                and (
                    not min_quantity
                    or min_quantity == 1
                    or (e.is_(Stackable) and e.Stackable.quantity >= min_quantity)
                )
            )

    def pick_nearby(self, selector, **kwargs):
        return self.pick(selector, self.nearby(), **kwargs)

    def pick_inventory(self, selector, **kwargs):
        return self.pick(selector, self.entity.Container.contents, **kwargs)

    def pick_from(self, selector, container, **kwargs):
        return self.pick(selector, container.Container.contents, **kwargs)

    def pick_nearby_inventory(self, selector, **kwargs):
        return self.pick(
            selector, self.entity.Container.contents | self.nearby(), **kwargs
        )

    #########################
    # Communication
    #########################

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

        messages = []

        if room.is_("Named"):
            messages.extend([string.capwords(room.Named.name), room.Named.desc])

        if room.is_(Exitable):
            exits = room.Exitable.exits
            if exits:
                messages.append("Exits:")
                for exit in exits:
                    name = "elsewhere"
                    if exit.Exit.destination.is_("Named"):
                        name = exit.Exit.destination.Named.name
                    messages.append(
                        indent("{0}: {1}".format(exit.Exit.direction, name))
                    )

        entities_nearby = [e for e in self.nearby() if not e.is_(Invisible)]
        if entities_nearby:
            messages.append("Things nearby:")
            for entity in entities_nearby:
                message = "something unnamed"
                if entity.is_("Named"):
                    message = entity.Named.name
                messages.append(indent(message))

        self.entity.tell("\n".join(messages))


def unique_selection(
    actor,
    action_name,
    argument_name,
    selector,
    kwargs,
    choices,
    area="in the area",
    quantity=None,
):
    if quantity is None:
        quantity = "any"

    if not choices:
        actor.tell("You don't see {0} '{1}' {2}.".format(quantity, selector, area))
        return False

    if len(choices) == 1:
        return True

    actor.mode = DisambiguationMode(
        action_name, argument_name, kwargs, [entity.id for entity in choices]
    )

    actor.tell("Which '{0}' do you mean?".format(selector))

    for index, entity in enumerate(choices):
        location = "in inventory" if entity.Spatial.container == actor else "nearby"
        actor.tell(
            indent("{0}. {1.Named.name} ({2})".format(index + 1, entity, location))
        )

    return False


#########################
# Actions
#########################


@ActionMode.action(r"^l(?:ook)?(?: around)?$")
def look(actor):
    if not actor.is_(Spatial):
        actor.tell("You're unable to do that.")
        return

    if actor.Spatial.container.is_("Dark"):
        actor.tell("It's too dark to see anything here.")
        return

    actor.Spatial.emit("{0.Named.Name} looks around.".format(actor))
    actor.Spatial.tell_surroundings()


@ActionMode.action(r"^l(?:ook)? (?:in(?:to|side(?: of)?)?) (?P<selector>.+)$")
def look_in(actor, selector):
    if not actor.is_(Spatial):
        actor.tell("You're unable to do that.")
        return

    targets = actor.Spatial.pick_nearby_inventory(selector)

    if not unique_selection(
        actor,
        "look_in",
        "selector",
        selector,
        {"selector": selector},
        targets,
        "nearby",
    ):
        return

    target = targets.pop()

    if not target.is_(Container):
        actor.tell("You can't look inside of that.")
        return

    if target.is_("Dark"):
        actor.tell("It's too dark in there to see anything.")
        return

    actor.tell("Contents:")

    contents = [e for e in target.Container.contents if not e.is_(Invisible)]
    if contents:
        for item in contents:
            # TODO FIXME: Assumes Named (see 'something unnamed' below)
            actor.tell(indent(item.Named.name))
    else:
        actor.tell(indent("nothing"))


@ActionMode.action(r"^(?:ex(?:amine)?|l(?:ook)?) (?:at )?(?P<selector>.+)$")
def look_at(actor, selector):
    if not actor.is_(Spatial):
        actor.tell("You're unable to do that.")
        return

    if actor.Spatial.container.is_("Dark"):
        actor.tell("It's too dark to see anything here.")
        return

    targets = actor.Spatial.pick_nearby_inventory(selector)

    if not unique_selection(
        actor,
        "look_at",
        "selector",
        selector,
        {"selector": selector},
        targets,
        "nearby",
    ):
        return

    target = targets.pop()

    actor.tell(target.Named.desc)
    actor.Spatial.emit(
        "{0.Named.Name} looks at {1.Named.name}.".format(actor, target), exclude=target
    )
    target.tell("{0.Named.Name} looks at you.".format(actor))


@ActionMode.action(
    r"^(?:get|take|pick up)( (?P<quantity>(?:\d+|all)))? (?P<selector>.+)$"
)
def get(actor, selector, quantity=None):
    if not actor.is_([Spatial, Container]):
        actor.tell("You're unable to do that.")
        return

    if quantity:
        quantity = Stackable.convert(quantity)

    targets = actor.Spatial.pick_nearby(selector, min_quantity=quantity)

    if not unique_selection(
        actor,
        "get",
        "selector",
        selector,
        {"selector": selector},
        targets,
        "nearby",
        quantity=quantity,
    ):
        return

    target = targets.pop()

    if target == actor:
        actor.tell("You can't put yourself in your inventory.")
        return

    if not target.is_([Spatial, Carriable]):
        actor.tell("That can't be carried.")
        return

    if target.is_("Important"):
        actor.tell("{0.Named.Name} resists your attempt to grab it.".format(target))
        return

    if target.is_("Stackable") and quantity is not None:
        quantity = target.Stackable.refine(quantity)

        if not quantity:
            actor.tell("You're unable to do that.")
            return

    target = actor.Container.store(target, quantity=quantity)

    actor.tell("You pick up {0.Named.name}.".format(target))
    actor.Spatial.emit(
        "{0.Named.Name} picks up {1.Named.name}.".format(actor, target), exclude=target
    )
    target.tell("{0.Named.Name} picks you up.".format(actor))

    if target.is_(Stackable):
        actor.Container.consolidate_contents()


@ActionMode.action(
    "^(?:get|take|pick up)( (?P<quantity>(?:\d+|all)))? (?P<target_selector>.+) from (?P<container_selector>.+)$"
)
def get_from(actor, target_selector, container_selector, quantity=None):
    kwargs = {
        "target_selector": target_selector,
        "container_selector": container_selector,
        "quantity": quantity,
    }

    if not actor.is_([Spatial, Container]):
        actor.tell("You're unable to hold items.")
        return

    containers = actor.Spatial.pick_nearby_inventory(container_selector)

    if not unique_selection(
        actor,
        "get_from",
        "container_selector",
        container_selector,
        kwargs,
        containers,
        "nearby",
    ):
        return

    container = containers.pop()

    if container == actor:
        actor.tell(
            "You can't get things from your inventory, they'd just go right back in!"
        )
        return

    if not container.is_([Spatial, Container]):
        actor.tell("{0.Named.Name} can't hold items.".format(container))
        return

    if quantity:
        quantity = Stackable.convert(quantity)

    targets = actor.Spatial.pick_from(target_selector, container, min_quantity=quantity)

    if not unique_selection(
        actor,
        "get_from",
        "target_selector",
        target_selector,
        kwargs,
        targets,
        "in {0.Named.name}".format(container),
        quantity=quantity,
    ):
        return

    target = targets.pop()

    if target == actor:
        actor.tell("You can't put yourself in your inventory.")
        return

    if not target.is_([Spatial, Carriable]):
        actor.tell(
            "You can't take {0.Named.name} from {1.Named.name}.".format(
                target, container
            )
        )
        return

    if target.is_("Important"):
        actor.tell("{0.Named.Name} resists your attempt to grab it.".format(target))
        return

    target = actor.Container.store(target, quantity=quantity)

    actor.tell("You take {0.Named.name} from {1.Named.name}.".format(target, container))
    actor.Spatial.emit(
        "{0.Named.Name} takes {1.Named.name} from {2.Named.name}.".format(
            actor, target, container
        ),
        exclude=(target, container),
    )
    container.tell(
        "{0.Named.Name} takes {1.Named.name} from you.".format(actor, target)
    )
    target.tell(
        "{0.Named.Name} takes you from {1.Named.name}.".format(actor, container)
    )

    if target.is_(Stackable):
        actor.Container.consolidate_contents()


@ActionMode.action(
    r"^put( (?P<quantity>(?:\d+|all)))? (?P<target_selector>.+) (?:in(?:to|side(?: of)?)?) (?P<container_selector>.+)$"
)
def put_in(actor, target_selector, container_selector, quantity=None):
    kwargs = {
        "target_selector": target_selector,
        "container_selector": container_selector,
        "quantity": quantity,
    }

    if not actor.is_([Spatial, Container]):
        actor.tell("You're unable to hold things.")
        return

    if quantity:
        quantity = Stackable.convert(quantity)

    targets = actor.Spatial.pick_nearby_inventory(
        target_selector, min_quantity=quantity
    )

    if not unique_selection(
        actor,
        "put_in",
        "target_selector",
        target_selector,
        kwargs,
        targets,
        "nearby",
        quantity=quantity,
    ):
        return

    target = targets.pop()

    if not target.is_(Spatial):
        actor.tell("You can't put {0.Named.name} into anything.")
        return

    if not target.is_([Carriable]):
        actor.tell("That can't be carried.")
        return

    if target.is_("Important"):
        actor.tell("You shouldn't get rid of this; it's very important.")
        return

    containers = actor.Spatial.pick_nearby_inventory(container_selector)

    if not unique_selection(
        actor,
        "put_in",
        "container_selector",
        container_selector,
        kwargs,
        containers,
        "nearby",
    ):
        return

    container = containers.pop()

    if not container.is_([Spatial, Container]):
        actor.tell("{0.Named.Name} can't hold things.".format(container))
        return

    if target.is_("Stackable") and quantity is not None:
        quantity = target.Stackable.refine(quantity)

        if not quantity:
            actor.tell("You're unable to do that.")
            return

    target = container.Container.store(target, quantity=quantity)

    actor.tell("You put {0.Named.name} in {1.Named.name}.".format(target, container))
    actor.Spatial.emit(
        "{0.Named.Name} puts {1.Named.name} in {2.Named.name}.".format(
            actor, target, container
        ),
        exclude=(target, container),
    )
    container.tell(
        "{0.Named.Name} puts {1.Named.name} in your inventory.".format(actor, target)
    )
    target.tell("{0.Named.Name} puts you in {1.Named.name}.".format(actor, container))

    if target.is_(Stackable):
        container.Container.consolidate_contents()


@ActionMode.action(r"^drop( (?P<quantity>(?:\d+|all)))? (?P<selector>.+)$")
def drop(actor, selector, quantity=None):
    if not actor.is_(Spatial):
        actor.tell("You're unable to drop things.")
        return

    if quantity:
        quantity = Stackable.convert(quantity)

    targets = actor.Spatial.pick_inventory(selector, min_quantity=quantity)

    if not unique_selection(
        actor,
        "drop",
        "selector",
        selector,
        {"selector": selector},
        targets,
        "in your inventory",
        quantity=quantity,
    ):
        return

    target = targets.pop()

    # TODO: other nearby stuff

    if target.is_("Important"):
        actor.tell("You shouldn't get rid of this; it's very important.")
        return

    if target.is_("Sticky") and not target.Sticky.roll_for_drop():
        actor.tell(
            "You try to drop {0.Named.name}, but it sticks to your hand.".format(target)
        )
        return

    if target.is_("Stackable") and quantity is not None:
        quantity = target.Stackable.refine(quantity)

        if not quantity:
            actor.tell("You're unable to do that.")
            return

    target = actor.Container.drop(target, quantity=quantity)

    actor.tell("You drop {0.Named.name}.".format(target))
    actor.Spatial.emit(
        "{0.Named.Name} drops {1.Named.name}.".format(actor, target), exclude=target
    )
    target.tell("{0.Named.Name} drops you.".format(actor))

    if target.is_(Stackable):
        actor.Spatial.container.Container.consolidate_contents()


@ActionMode.action("^(?:w(?:alk)?|go) (?P<direction>.+)$")
def walk(actor, direction):
    if not actor.is_(Spatial):
        actor.tell("You're unable to move.")
        return

    room = actor.Spatial.container

    # Actor is hanging out at the top level, or room is in a bad state
    if not room or not room.is_(Spatial):
        actor.tell("You're unable to leave this place.")
        return

    exits = []
    if room.is_(Exitable):
        exits = room.Exitable.exits

    if not exits:
        actor.tell("There don't seem to be any exits here.")
        return

    for exit in exits:
        if direction.lower() == exit.Exit.direction.lower():
            destination = exit.Exit.destination
            break
    else:
        actor.tell("You're unable to go that way.")
        return

    # Ensure the destination is still a container
    if not destination or not destination.is_([Spatial, Container]):
        actor.tell("You're unable to go that way.")
        return

    actor.tell("You travel {0}.".format(direction))
    actor.Spatial.emit(
        "{0.Named.Name} travels {1} to {2.Named.name}.".format(
            actor, direction, destination
        )
    )
    destination.Container.announce(
        "{0.Named.Name} arrives from {1.Named.name}.".format(actor, room)
    )
    destination.Container.store(actor)

    actor.Spatial.tell_surroundings()


@ActionMode.action(r"^enter (?P<selector>.+)$")
def enter(actor, selector):
    if not actor.is_(Spatial):
        actor.tell("You're unable to move.")
        return

    room = actor.Spatial.container

    # Actor is hanging out at the top level, or room is in a bad state
    if not room or not room.is_(Spatial):
        actor.tell("You're unable to leave this place.")
        return

    containers = actor.Spatial.pick_nearby(selector)

    if not unique_selection(
        actor,
        "enter",
        "selector",
        selector,
        {"selector": selector},
        containers,
        "nearby",
    ):
        return

    container = containers.pop()

    if not container.is_([Spatial, Enterable, Container]):
        actor.tell("You can't enter that.")
        return

    actor.tell("You enter {0.Named.name}.".format(container))
    actor.Spatial.emit("{0.Named.Name} enters {1.Named.name}.".format(actor, container))
    container.Container.announce(
        "{0.Named.Name} arrives from {1.Named.name}.".format(actor, room)
    )
    container.Container.store(actor)

    actor.Spatial.tell_surroundings()


##########################
# Aliases and shortcuts
##########################


@ActionMode.action("^(?:i|inv|inventory)$")
def tell_inventory(actor):
    return actor.perform("look in self")


@ActionMode.action("^n(?:orth)?$")
def go_north(actor):
    return actor.perform("go north")


@ActionMode.action("^s(?:outh)?$")
def go_south(actor):
    return actor.perform("go south")


@ActionMode.action("^e(?:ast)?$")
def go_east(actor):
    return actor.perform("go east")


@ActionMode.action("^w(?:est)?$")
def go_west(actor):
    return actor.perform("go west")


@ActionMode.action("^(?:ne|northeast)$")
def go_northeast(actor):
    return actor.perform("go northeast")


@ActionMode.action("^(?:nw|northwest)$")
def go_northwest(actor):
    return actor.perform("go northwest")


@ActionMode.action("^(?:se|southeast)$")
def go_southeast(actor):
    return actor.perform("go southeast")


@ActionMode.action("^(?:sw|southwest)$")
def go_southwest(actor):
    return actor.perform("go southwest")


@ActionMode.action("^u(?:p)?$")
def go_up(actor):
    return actor.perform("go up")


@ActionMode.action("^d(?:own)?$")
def go_down(actor):
    return actor.perform("go down")


#########################
# Dialogue actions
#########################


def dialogue(actor, second_person_verb, third_person_verb, message):
    if not actor.is_(Spatial):
        actor.tell("You're unable to do that.")
        return

    message = upper_first(message.strip().replace('"', "'"))

    if not message[-1] in (".", "?", "!"):
        message += "."

    actor.tell('You {0}: "{1}"'.format(second_person_verb, message))
    actor.Spatial.emit(
        '{0.Named.Name} {1}: "{2}"'.format(actor, third_person_verb, message)
    )


@ActionMode.action(r"^s(?:ay)? (?P<message>.+)$")
def say(actor, message):
    dialogue(actor, "say", "says", message)


@ActionMode.action(r"^shout (?P<message>.+)$")
def shout(actor, message):
    dialogue(actor, "shout", "shouts", message)


@ActionMode.action(r"^sing (?P<message>.+)$")
def sing(actor, message):
    dialogue(actor, "sing", "sings", message)


@ActionMode.action(r"^growl (?P<message>.+)$")
def growl(actor, message):
    dialogue(actor, "growl", "growls", message)
