from schema import Entity, Event, Zone
from tests.helpers import tell, saw, Visible, Colorful, BlackHole

class TestEntity(object):
    @classmethod
    def setup_class(cls):
        Entity.tell = tell
        Entity.saw = saw

    def setup(self):
        self.zone = z = Zone()

        # TODO: This is ugly
        Event.witnesses = lambda s: z.all()

        self.player = Entity('Player', 'A player stands here.', [Visible()], zone=z)
        self.ball = Entity('a ball', 'A round plastic ball.', [
            Visible(), Colorful(color='red')
        ], zone=z)
        self.bh = Entity('black hole', 'This text should never appear.', [
            Visible(), Colorful(color='black'), BlackHole()
        ], zone=z)

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
