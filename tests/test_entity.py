from figment import Entity, Event, Zone
from tests.helpers import tell, saw, Visible, Colorful, BlackHole


class TestEntity(object):
    @classmethod
    def setup_class(cls):
        Entity.tell = tell
        Entity.saw = saw

    def setup(self):
        self.zone = z = Zone()
        self.player = Entity(
            'Player', 'A player stands here.', [Visible()], zone=z
        )
        self.ball = Entity('a ball', 'A round rubber ball.', [
            Visible(), Colorful(color='red')
        ], zone=z)
        self.bh = Entity('black hole', 'This text should never appear.', [
            Visible(), Colorful(color='black'), BlackHole()
        ], zone=z)
        self.cow = Entity('a cow', 'A wild dairy cow.', [Visible()], zone=z)

    def test_look_at(self):
        self.player.perform('look at %s' % self.ball.id)
        assert self.player.saw('rubber ball')

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
        assert self.player.saw('unable to look directly')

    def test_color_of_uncolorful(self):
        self.player.perform('color of %s' % self.cow.id)
        assert self.player.saw('no particular')

    def test_paint_unpaintable(self):
        self.player.perform('paint %s orange' % self.cow.id)
        assert self.player.saw('cannot be painted')

    def test_add_aspect(self):
        self.cow.aspects.add(Colorful(color='green'))
        self.player.perform('color of %s' % self.cow.id)
        assert self.player.saw('green')

    def test_remove_aspect(self):
        self.ball.aspects.remove(Colorful)
        self.player.perform('color of %s' % self.ball.id)
        assert self.player.saw('no particular')

    def test_perform_with_action_and_event(self):
        self.player.perform(Visible.look_at, descriptor=self.ball.id)
        assert self.player.saw('rubber')
