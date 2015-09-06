from figment import Component
from components import Position
from modes import ActionMode

class Emotive(Component):
    """Enables an entity to emote."""

def emote(actor, verb, plural=None, join=None, selector=None):
    if not plural:
        plural = verb + 's'

    if not actor.is_([Position, Emotive]):
        actor.tell("You're unable to do that.")
        return

    if not selector:
        actor.Position.emit('{0.Name} {1}.'.format(actor, plural))
        actor.tell('You {0}.'.format(verb))
        return

    target = actor.Position.pick_nearby(selector)
    if not target:
        return

    if join:
        actor.Position.emit('{0.Name} {1} {2} {3.name}.'.format(actor, plural, join, target), exclude=target)
        actor.tell('You {0} {1} {2.name}.'.format(verb, join, target))
        target.tell('{0.Name} {1} {2} you.'.format(actor, plural, join))
    else:
        actor.Position.emit('{0.Name} {1} {2.name}.'.format(actor, plural, target), exclude=target)
        actor.tell('You {0} {1.name}.'.format(verb, target))
        target.tell('{0.Name} {1} you.'.format(actor, plural))

@ActionMode.action(r'^dance(?: with (?P<selector>.+))?$')
def dance(actor, selector=None):
    return emote(actor, 'dance', join='with', selector=selector)

@ActionMode.action(r'^laugh(?: at (?P<selector>.+))?$')
def laugh(actor, selector=None):
    return emote(actor, 'laugh', join='at', selector=selector)

@ActionMode.action(r'^lol$')
def lol(actor):
    return emote(actor, 'laugh')

@ActionMode.action(r'^blink(?: at (?P<selector>.+))?$')
def blink(actor, selector=None):
    return emote(actor, 'blink', join='at', selector=selector)

@ActionMode.action(r'^frown(?: at (?P<selector>.+))?$')
def frown(actor, selector=None):
    return emote(actor, 'frown', join='at', selector=selector)

@ActionMode.action(r'^scowl(?: at (?P<selector>.+))?$')
def scowl(actor, selector=None):
    return emote(actor, 'scowl', join='at', selector=selector)

@ActionMode.action(r'^eyebrow(?: at (?P<selector>.+))?$')
def eyebrow(actor, selector=None):
    return emote(actor, 'raise an eyebrow', 'raises an eyebrow', join='at', selector=selector)

@ActionMode.action(r'^shrug(?: at (?P<selector>.+))?$')
def shrug(actor, selector=None):
    return emote(actor, 'shrug', join='at', selector=selector)

@ActionMode.action(r'^smile(?: at (?P<selector>.+))?$')
def smile(actor, selector=None):
    return emote(actor, 'smile', join='at', selector=selector)

@ActionMode.action(r'^grin(?: at (?P<selector>.+))?$')
def grin(actor, selector=None):
    return emote(actor, 'grin', join='at', selector=selector)

@ActionMode.action(r'^bow(?: to (?P<selector>.+))?$')
def bow(actor, selector=None):
    return emote(actor, 'bow', join='to', selector=selector)

@ActionMode.action(r'^nod(?: (?P<join>at|to) (?P<selector>.+))?$')
def nod(actor, join=None, selector=None):
    return emote(actor, 'nod', join=join, selector=selector)

@ActionMode.action(r'^cheer(?: for (?P<selector>.+))?$')
def cheer(actor, selector=None):
    return emote(actor, 'cheer', join='for', selector=selector)

@ActionMode.action(r'^cough(?: (?P<join>on|at) (?P<selector>.+))?$')
def cough(actor, join=None, selector=None):
    return emote(actor, 'cough', join=join, selector=selector)

@ActionMode.action(r'^cry(?: on (?P<selector>.+))?$')
def cry(actor, selector=None):
    return emote(actor, 'cry', 'cries', join='on', selector=selector)

@ActionMode.action(r'^point(?: (?P<join>to|at) (?P<selector>.+))?$')
def point(actor, join=None, selector=None):
    return emote(actor, 'point', join=join, selector=selector)

@ActionMode.action(r'^wave(?: (?P<join>to|at) (?P<selector>.+))?$')
def wave(actor, join=None, selector=None):
    return emote(actor, 'wave', join=join, selector=selector)

@ActionMode.action(r'^wink(?: (?P<join>to|at) (?P<selector>.+))?$')
def wink(actor, join=None, selector=None):
    return emote(actor, 'wink', join=join, selector=selector)

@ActionMode.action(r'^poke (?P<selector>.+)$')
def poke(actor, selector):
    return emote(actor, 'poke', selector=selector)

@ActionMode.action(r'^hug (?P<selector>.+)$')
def hug(actor, selector):
    return emote(actor, 'hug', selector=selector)

@ActionMode.action(r'^kiss (?P<selector>.+)$')
def kiss(actor, selector):
    return emote(actor, 'kiss', 'kisses', selector=selector)
