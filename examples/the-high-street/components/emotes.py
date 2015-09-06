from figment import Component, action
from components import Position

class Emotes(Component):
    """Enables an entity to emote."""

    @staticmethod
    def emote(event, verb, plural=None, join=None):
        if not plural:
            plural = verb + 's'

        if not event.actor.has_component([Position, Emotes]):
            event.actor.tell("You're unable to do that.")
            return

        if not event.selector:
            event.actor.Position.emit('{0.Name} {1}.'.format(event.actor, plural))
            event.actor.tell('You {0}.'.format(verb))
            return

        event.target = event.actor.Position.pick_nearby(event.selector)
        if not event.target:
            return

        yield 'before'
        if event.data.get('prevented'):
            return

        if join:
            event.actor.Position.emit('{0.Name} {1} {2} {3.name}.'.format(event.actor, plural, join, event.target), exclude=event.target)
            event.actor.tell('You {0} {1} {2.name}.'.format(verb, join, event.target))
            event.target.tell('{0.Name} {1} {2} you.'.format(event.actor, plural, join))
        else:
            event.actor.Position.emit('{0.Name} {1} {2.name}.'.format(event.actor, plural, event.target), exclude=event.target)
            event.actor.tell('You {0} {1.name}.'.format(verb, event.target))
            event.target.tell('{0.Name} {1} you.'.format(event.actor, plural))

    @action(r'^dance(?: with (?P<selector>.+))?$')
    def dance(event):
        return Emotes.emote(event, 'dance', join='with')

    @action(r'^laugh(?: at (?P<selector>.+))?$')
    def laugh(event):
        return Emotes.emote(event, 'laugh', join='at')

    @action(r'^lol$')
    def lol(event):
        return Emotes.emote(event, 'laugh')

    @action(r'^blink(?: at (?P<selector>.+))?$')
    def blink(event):
        return Emotes.emote(event, 'blink', join='at')

    @action(r'^frown(?: at (?P<selector>.+))?$')
    def frown(event):
        return Emotes.emote(event, 'frown', join='at')

    @action(r'^scowl(?: at (?P<selector>.+))?$')
    def scowl(event):
        return Emotes.emote(event, 'scowl', join='at')

    @action(r'^eyebrow(?: at (?P<selector>.+))?$')
    def eyebrow(event):
        return Emotes.emote(event, 'raise an eyebrow', 'raises an eyebrow', join='at')

    @action(r'^shrug(?: at (?P<selector>.+))?$')
    def shrug(event):
        return Emotes.emote(event, 'shrug', join='at')

    @action(r'^smile(?: at (?P<selector>.+))?$')
    def smile(event):
        return Emotes.emote(event, 'smile', join='at')

    @action(r'^grin(?: at (?P<selector>.+))?$')
    def grin(event):
        return Emotes.emote(event, 'grin', join='at')

    @action(r'^bow(?: to (?P<selector>.+))?$')
    def bow(event):
        return Emotes.emote(event, 'bow', join='to')

    @action(r'^nod(?: (?P<join>at|to) (?P<selector>.+))?$')
    def nod(event):
        return Emotes.emote(event, 'nod', join=event.join)

    @action(r'^cheer(?: for (?P<selector>.+))?$')
    def cheer(event):
        return Emotes.emote(event, 'cheer', join='for')

    @action(r'^cough(?: (?P<join>on|at) (?P<selector>.+))?$')
    def cough(event):
        return Emotes.emote(event, 'cough', join=event.join)

    @action(r'^cry(?: on (?P<selector>.+))?$')
    def cry(event):
        return Emotes.emote(event, 'cry', 'cries', join='on')

    @action(r'^point(?: (?P<join>to|at) (?P<selector>.+))?$')
    def point(event):
        return Emotes.emote(event, 'point', join=event.join)

    @action(r'^wave(?: (?P<join>to|at) (?P<selector>.+))?$')
    def wave(event):
        return Emotes.emote(event, 'wave', join=event.join)

    @action(r'^wink(?: (?P<join>to|at) (?P<selector>.+))?$')
    def wink(event):
        return Emotes.emote(event, 'wink', join=event.join)

    @action(r'^poke (?P<selector>.+)$')
    def poke(event):
        return Emotes.emote(event, 'poke')

    @action(r'^hug (?P<selector>.+)$')
    def hug(event):
        return Emotes.emote(event, 'hug')

    @action(r'^kiss (?P<selector>.+)$')
    def kiss(event):
        return Emotes.emote(event, 'kiss', 'kisses')
