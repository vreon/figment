def upper_first(value):
    return "".join((value[0].upper(), value[1:]))


def indent(value, depth=1):
    return "".join((" " * 4 * depth, value))
