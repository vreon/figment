from schema import Aspect
from .positioned import Positioned

class Emotes(Aspect):
    """Enables an entity to emote."""
    requires = [Positioned]

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

    @action(r'^dance(?: with (?P<target>.+))?$')
    def dance(self, event):
        self.emote(event.target, 'dance', join='with')

    @action(r'^laugh(?: at (?P<target>.+))?$')
    def laugh(self, event):
        self.emote(event.target, 'laugh')

    @action(r'^lol$')
    def lol(self):
        self.laugh(None)

    @action(r'^blink(?: at (?P<target>.+))?$')
    def blink(self, event):
        self.emote(event.target, 'blink')

    @action(r'^frown(?: at (?P<target>.+))?$')
    def frown(self, event):
        self.emote(event.target, 'frown')

    @action(r'^eyebrow(?: at (?P<target>.+))?$')
    def eyebrow(self, event):
        self.emote(event.target, 'raise an eyebrow', 'raises an eyebrow')

    @action(r'^shrug(?: at (?P<target>.+))?$')
    def shrug(self, event):
        self.emote(event.target, 'shrug')

    @action(r'^smile(?: at (?P<target>.+))?$')
    def smile(self, event):
        self.emote(event.target, 'smile')

    @action(r'^grin(?: at (?P<target>.+))?$')
    def grin(self, event):
        self.emote(event.target, 'grin')

    @action(r'^bow(?: to (?P<target>.+))?$')
    def bow(self, event):
        self.emote(event.target, 'bow', join='to')

    @action(r'^nod(?: (?P<join>at|to) (?P<target>.+))?$')
    def nod(self, event):
        self.emote(event.target, 'nod', join=event.join.value)

    @action(r'^cheer(?: for (?P<target>.+))?$')
    def cheer(self, event):
        self.emote(event.target, 'cheer', join='for')

    @action(r'^cough(?: (?P<join>on|at) (?P<target>.+))?$')
    def cough(self, event):
        self.emote(event.target, 'cough', join=event.join.value)

    @action(r'^cry(?: on (?P<target>.+))?$')
    def cry(self, event):
        self.emote(event.target, 'cry', 'cries', join='on')

    @action(r'^point(?: (?P<join>to|at) (?P<target>.+))?$')
    def point(self, event):
        self.emote(event.target, 'point', join=event.join.value)

    @action(r'^wave(?: (?P<join>to|at) (?P<target>.+))?$')
    def wave(self, event):
        self.emote(event.target, 'wave', join=event.join.value)

    @action(r'^wink(?: (?P<join>to|at) (?P<target>.+))?$')
    def wink(self, event):
        self.emote(event.target, 'wink', join=event.join.value)
