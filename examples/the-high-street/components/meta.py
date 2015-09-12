import json
from figment import Component
from figment.utils import indent
from modes import ActionMode

class Meta(Component):
    """Enables an entity to use meta commands."""

class Admin(Component):
    """Enables an entity to use admin commands."""

    def __init__(self, aliases={}):
        self.aliases = aliases

    def to_dict(self):
        return {
            'aliases': self.aliases,
        }

    @classmethod
    def from_dict(cls, dict_):
        return cls(
            aliases=dict_['aliases'],
        )


@ActionMode.action(r'^!connect$')
def connect(actor):
    if not actor.is_(Meta):
        actor.tell("You're unable to do that.")
        return

    actor.tell("Welcome to The High Street, {0.Name}.".format(actor))

@ActionMode.action(r'^!q(?:uery)?$')
def query(actor):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    for entity in actor.zone.all():
        actor.tell('[{0.id}] "{0.name}"'.format(entity))


@ActionMode.action(r'^!i(?:nspect)? (?P<entity_id>.+)$')
def inspect(actor, entity_id):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    entity_id = actor.Admin.aliases.get(entity_id, entity_id)
    entity = actor.zone.get(entity_id)

    if entity is None:
        actor.tell('No such entity.')
        return

    actor.tell('[{0.id}] "{0.name}"'.format(entity))

    actor.tell(indent('name: {0}', depth=1).format(json.dumps(entity.name)))
    actor.tell(indent('desc: {0}', depth=1).format(json.dumps(entity.desc)))
    actor.tell(indent('hearing: {0}', depth=1).format(json.dumps(entity.hearing)))

    for component in entity.components:
        actor.tell(indent('{0}').format(component.__class__.__name__))
        for key, value in component.to_dict().items():
            actor.tell(indent('{0}: {1}', depth=2).format(key, json.dumps(value)))


@ActionMode.action(r'^!e(?:dit)? (?P<entity_id>.+) detach (?P<component_class_name>.+)$')
def detach(actor, entity_id, component_class_name, arguments=None):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    entity_id = actor.Admin.aliases.get(entity_id, entity_id)
    entity = actor.zone.get(entity_id)

    if entity is None:
        actor.tell('No such entity "{0}".'.format(entity_id))
        return

    component_class = entity.zone.components.get(component_class_name)

    if component_class is None:
        actor.tell('No such component "{0}".'.format(component_class_name))
        return

    if not entity.is_(component_class):
        actor.tell('[{0.id}] "{0.name}" has no component "{1}".'.format(entity, component_class_name))
        return

    entity.components.remove(component_class)
    actor.tell('[{0.id}] "{0.name}" is no longer "{1}".'.format(entity, component_class_name))


@ActionMode.action(r'^!e(?:dit)? (?P<entity_id>.+) attach (?P<component_class_name>.+?)(?: (?P<arguments>.+))?$')
def attach(actor, entity_id, component_class_name, arguments=None):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    entity_id = actor.Admin.aliases.get(entity_id, entity_id)
    entity = actor.zone.get(entity_id)

    if entity is None:
        actor.tell('No such entity "{0}".'.format(entity_id))
        return

    component_class = entity.zone.components.get(component_class_name)

    if component_class is None:
        actor.tell('No such component "{0}".'.format(component_class_name))
        return

    if entity.is_(component_class):
        actor.tell('[{0.id}] "{0.name}" already has component "{1}".'.format(entity, component_class_name))
        return

    if arguments is None:
        arguments = '{}'

    try:
        component = component_class.from_dict(json.loads(arguments))
    except Exception as e:
        actor.tell('[{0.id}] "{0.name}" failed to attach "{1}":'.format(entity, component_class_name))
        actor.tell(indent(str(e)))
        return

    entity.components.add(component)
    actor.tell('[{0.id}] "{0.name}" is now "{1}".'.format(entity, component_class_name))


@ActionMode.action(r'^!e(?:dit)? (?P<entity_id>.+) set (?P<attribute>.+?) (?P<value>.+)$')
def set_attribute(actor, entity_id, attribute, value):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    entity_id = actor.Admin.aliases.get(entity_id, entity_id)
    entity = actor.zone.get(entity_id)

    if entity is None:
        actor.tell('No such entity "{0}".'.format(entity_id))
        return

    try:
        value = json.loads(value)
    except Exception as e:
        actor.tell('[{0.id}] "{0.name}" failed to set "{1}":'.format(entity, attribute))
        actor.tell(indent(str(e)))
        return

    if attribute == 'name':
        entity.name = value
    elif attribute in ['desc', 'description']:
        entity.desc = value
    elif attribute == 'hearing':
        entity.hearing = value
    else:
        # TODO: Components
        # Split attribute on dot
        pass

    actor.tell('OK.')


@ActionMode.action(r'^!s(?:pawn)?(?: (?P<template>.+))?$')
def spawn(actor, template=None):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    # TODO: handle templates

    entity = actor.zone.spawn('an entity', 'A nondescript thing.')
    actor.tell('Spawned [{0.id}] "{0.name}".'.format(entity))


@ActionMode.action(r'^!d(?:estroy)? (?P<entity_id>.+)$')
def destroy(actor, entity_id):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    entity_id = actor.Admin.aliases.get(entity_id, entity_id)
    entity = actor.zone.get(entity_id)

    if entity is None:
        actor.tell('No such entity.')
        return

    entity.destroy()
    actor.tell('Destroyed [{0.id}] "{0.name}".'.format(entity))


@ActionMode.action(r'^!a(?:lias)? (?:add|create) (?P<alias>.+) (?P<entity_id>.+)$')
def add_alias(actor, alias, entity_id):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    actor.Admin.aliases[alias] = entity_id


@ActionMode.action(r'^!a(?:lias)? (rm|remove|del(ete)?) (?P<alias>.+)$')
def remove_alias(actor, alias):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    actor.Admin.aliases.pop(alias, None)


@ActionMode.action(r'^!a(?:lias)?(?: list)?$')
def list_aliases(actor):
    if not actor.is_(Admin):
        actor.tell("You're unable to do that.")
        return

    for alias, entity_id in actor.Admin.aliases.items():
        entity = actor.zone.get(entity_id)
        if entity:
            actor.tell('{0}: [{1.id}] "{1.name}"'.format(alias, entity))
        else:
            actor.tell('{0}: {1}'.format(alias, entity_id))
