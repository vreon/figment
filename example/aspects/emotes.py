from schema import Aspect, action
from .positioned import Positioned

class Emotes(Aspect):
    """Enables an entity to emote."""

    @staticmethod
    def emote(event, verb, plural=None, join=None):
        if not plural:
            plural = verb + 's'

        if not event.actor.has_aspect([Positioned, Emotes]):
            event.actor.tell("You're unable to do that.")
            return

        if not event.descriptor:
            event.actor.Positioned.emit('{0.Name} {1}.'.format(event.actor, plural))
            event.actor.tell('You {0}.'.format(verb))
            return

        target = event.actor.Positioned.pick_nearby(event.descriptor)
        if not target:
            return

        event.trigger('before')
        if event.prevented:
            return

        if join:
            event.actor.Positioned.emit('{0.Name} {1} {2} {3.name}.'.format(event.actor, plural, join, target), exclude=target)
            event.actor.tell('You {0} {1} {2.name}.'.format(verb, join, target))
            target.tell('{0.Name} {1} {2} you.'.format(event.actor, plural, join))
        else:
            event.actor.Positioned.emit('{0.Name} {1} {2.name}.'.format(event.actor, plural, target), exclude=target)
            event.actor.tell('You {0} {1.name}.'.format(verb, target))
            target.tell('{0.Name} {1} you.'.format(event.actor, plural))

    @action(r'^dance(?: with (?P<descriptor>.+))?$')
    def dance(event):
        Emotes.emote(event, 'dance', join='with')

    @action(r'^laugh(?: at (?P<descriptor>.+))?$')
    def laugh(event):
        Emotes.emote(event, 'laugh', join='at')

    @action(r'^lol$')
    def lol(event):
        Emotes.emote(event, 'laugh')

    @action(r'^blink(?: at (?P<descriptor>.+))?$')
    def blink(event):
        Emotes.emote(event, 'blink', join='at')

    @action(r'^frown(?: at (?P<descriptor>.+))?$')
    def frown(event):
        Emotes.emote(event, 'frown', join='at')

    @action(r'^eyebrow(?: at (?P<descriptor>.+))?$')
    def eyebrow(event):
        Emotes.emote(event, 'raise an eyebrow', 'raises an eyebrow', join='at')

    @action(r'^shrug(?: at (?P<descriptor>.+))?$')
    def shrug(event):
        Emotes.emote(event, 'shrug', join='at')

    @action(r'^smile(?: at (?P<descriptor>.+))?$')
    def smile(event):
        Emotes.emote(event, 'smile', join='at')

    @action(r'^grin(?: at (?P<descriptor>.+))?$')
    def grin(event):
        Emotes.emote(event, 'grin', join='at')

    @action(r'^bow(?: to (?P<descriptor>.+))?$')
    def bow(event):
        Emotes.emote(event, 'bow', join='to')

    @action(r'^nod(?: (?P<join>at|to) (?P<descriptor>.+))?$')
    def nod(event):
        Emotes.emote(event, 'nod', join=event.join.value)

    @action(r'^cheer(?: for (?P<descriptor>.+))?$')
    def cheer(event):
        Emotes.emote(event, 'cheer', join='for')

    @action(r'^cough(?: (?P<join>on|at) (?P<descriptor>.+))?$')
    def cough(event):
        Emotes.emote(event, 'cough', join=event.join.value)

    @action(r'^cry(?: on (?P<descriptor>.+))?$')
    def cry(event):
        Emotes.emote(event, 'cry', 'cries', join='on')

    @action(r'^point(?: (?P<join>to|at) (?P<descriptor>.+))?$')
    def point(event):
        Emotes.emote(event, 'point', join=event.join.value)

    @action(r'^wave(?: (?P<join>to|at) (?P<descriptor>.+))?$')
    def wave(event):
        Emotes.emote(event, 'wave', join=event.join.value)

    @action(r'^wink(?: (?P<join>to|at) (?P<descriptor>.+))?$')
    def wink(event):
        Emotes.emote(event, 'wink', join=event.join.value)

    @action(r'^poke (?P<descriptor>.+)$')
    def poke(event):
        Emotes.emote(event, 'poke')

    @action(r'^hug (?P<descriptor>.+)$')
    def hug(event):
        Emotes.emote(event, 'hug')

    @action(r'^kiss (?P<descriptor>.+)$')
    def kiss(event):
        Emotes.emote(event, 'kiss', 'kisses')
