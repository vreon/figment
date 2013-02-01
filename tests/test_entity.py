from schema import Entity, Event
from tests.helpers import tell, saw, Visible, Colorful, BlackHole

class TestEntity(object):
    @classmethod
    def setup_class(cls):
        Entity.tell = tell
        Entity.saw = saw
        Event.witnesses = lambda s: Entity.ALL.values()

    def setup(self):
        self.player = Entity('Player', 'A player stands here.', [Visible()])
        self.ball = Entity('a ball', 'A round plastic ball.', [
            Visible(), Colorful(color='red')
        ])
        self.bh = Entity('black hole', 'This text should never appear.', [
            Visible(), Colorful(color='black'), BlackHole()
        ])

    def teardown(self):
        ids = Entity.ALL.keys()
        for id in ids:
            Entity.get(id).destroy()

    def test_look_at(self):
        self.player.perform('look at %s' % self.ball.id)
        assert self.player.saw('plastic ball')

    def test_color(self):
        self.player.perform('color of %s' % self.ball.id)
        assert self.player.saw('red')

    def test_paint(self):
        self.player.perform('paint %s blue' % self.ball.id)
        assert self.player.saw('blue')

    def test_absorb_paint(self):
        self.player.perform('paint %s blue' % self.bh.id)
        assert self.player.saw('black')

    def test_look_at_override(self):
        self.player.perform('look at %s' % self.bh.id)
        assert self.player.saw('unable')
