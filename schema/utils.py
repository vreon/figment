from schema.entity import Entity

def int_or_none(value):
    try:
        value = int(value)
        return value
    except (TypeError, ValueError):
        pass

def upper_first(value):
    return ''.join((value[0].upper(), value[1:]))

def str_to_bool(value):
    return value == 'True'

def indent(value, depth=1):
    return ''.join((' ' * 4 * depth, value))

def to_id(entity_or_id):
    if isinstance(entity_or_id, Entity):
        return entity_or_id.id
    return entity_or_id


def to_entity(entity_or_id):
    if isinstance(entity_or_id, Entity):
        return entity_or_id
    return Entity.get(entity_or_id)
