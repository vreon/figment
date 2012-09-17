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

def indent(value):
    return ''.join((' ' * 4, value))
