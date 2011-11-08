from schema import World, Clock
from schema.entity import Entity
from schema.component import *

def inside(ent, container_ent):
    """Returns True if the entity is inside the container."""
    return container_ent.is_(Container) and ent in container_ent[Container].contents

class TestWorld(object):
    def setup(self):
        self.world = World()

        self.rooms['room'] = {
            'name': 'The Test Room',
            'desc': 'A nondescript room for testing.',
        }

        # Knock out the old clock and replace it with an instant one
        self.world.clock = Clock(self.world.tick, 0)

        # Create a default player
        self.player = self.world.player = Entity('self', "Yep, that's you.")
        self.player.is_now(Positionable, 'room')
        self.player.is_now(Massive, 75)
        self.player.is_now(Voluminous, 8000)
        self.player.is_now(Damageable)
        self.player[Damageable].scale[Damageable.DamageType.ELECTRICAL] = 1.0
        self.player.is_now(Container, 5000, 20)
        self.player.is_now(Flammable)
        self.player.is_now(Soakable)
        self.world.entities.append(self.player)

        # Create some basic entities
        # Save them all to the fixture for convenience
        self.thingy = Entity()
        self.thingy.is_now(Positionable, 'room')
        self.thingy.is_now(Storable)
        self.world.entities.append(self.thingy)

        self.crate = Entity('large crate')
        self.crate.is_now(Positionable, 'room')
        self.crate.is_now(Massive, 77)
        self.crate.is_now(Damageable, 40)
        self.crate.is_now(Flammable)
        self.crate.is_now(Voluminous, 500000)
        self.crate.is_now(Container, 499000)
        self.world.entities.append(self.crate)

        self.sphere = Entity('sphere', 'A weighted metal sphere of some sort.')
        self.sphere.is_now(Positionable, 'room')
        self.sphere.is_now(Massive, 9)
        self.sphere.is_now(Damageable, 500)
        self.sphere.is_now(Storable)
        self.sphere.is_now(Voluminous, 4000)
        self.world.entities.append(self.sphere)

        self.backpack = Entity('backpack')
        self.backpack.is_now(Positionable, 'room')
        self.backpack.is_now(Massive, 0.5)
        self.backpack.is_now(Damageable, 40)
        self.backpack.is_now(Flammable)
        self.backpack.is_now(Soakable)
        self.backpack.is_now(Storable)
        self.backpack.is_now(Voluminous, 5000)
        self.backpack.is_now(Container, 5000)
        self.world.entities.append(self.backpack)

    @property
    def out(self):
        return '\n'.join(self.world.output)

    def flush(self):
        while self.world.output:
            self.world.output.popleft()

    def cmd(self, cmd):
        self.world.command(cmd)

    def test_create_world(self):
        """Creation of worlds"""
        assert self.player in self.world.entities
        assert 'Welcome' in self.out

    def test_proximity(self):
        """Getting objects nearby"""
        assert self.sphere in self.world._ents_near(self.player)
        assert self.backpack in self.world._ents_near(self.crate)

    def test_run_command(self):
        """Commands produce output"""
        self.cmd('look')
        assert self.out

    def test_run_invalid_command(self):
        """Invalid commands produce failure messages"""
        self.cmd('blooorf')
        assert 'can\'t' in self.out

    def test_look_around(self):
        """Seeing nearby entities"""
        self.cmd('look')
        assert 'self' in self.out
        assert 'thingy' in self.out
        assert 'crate' in self.out

    def test_look_at_self(self):
        """The player is visible"""
        self.cmd('look self')
        assert 'Yep' in self.out
        self.flush()
        self.cmd('look at myself')
        assert 'Yep' in self.out

    def test_look_at_entity(self):
        """Looking at a particular entity"""
        self.cmd('look at sphere')
        assert 'weighted' in self.out

    def test_look_at_nonexistent(self):
        """Looking at something that doesn't exist"""
        self.cmd('look at blorf')
        assert 'no blorf nearby' in self.out

    def test_look_in_container(self):
        """Looking inside a container"""
        self.cmd('look in crate')
        assert 'nothing' in self.out

    def test_look_in_noncontainer(self):
        """Try to look inside something that's not a container"""
        self.cmd('look in sphere')
        assert 'can\'t' in self.out

    def test_examine(self):
        """Examining entities in detail"""
        self.cmd('examine self')
        assert 'flammable' in self.out
        self.cmd('examine backpack')
        assert '40/40' in self.out

    def test_get_nearby(self):
        """Pick up an entity"""
        self.cmd('get sphere')
        assert inside(self.sphere, self.player)
        assert 'pick up' in self.out

    def test_get_unstorable(self):
        """Try to pick up something that you can't"""
        self.cmd('get crate')
        assert not inside(self.crate, self.player)

    def test_put_in_container(self):
        """Try to put something in a container"""
        self.cmd('put sphere in crate')
        assert inside(self.sphere, self.crate)
        self.flush()
        self.cmd('look in crate')
        assert 'sphere' in self.out

    def test_put_in_noncontainer(self):
        """Try to put something in a noncontainer"""
        self.cmd('put thingy in sphere')
        assert not inside(self.thingy, self.sphere)
        self.flush()
        self.cmd('look')
        assert 'thingy' in self.out

    def test_get_from_container(self):
        """Get something out of a container"""
        self.cmd('put sphere in crate')
        self.cmd('get sphere from crate')
        assert not inside(self.sphere, self.crate)

    def test_put_container_droste(self):
        """Try to put a container in itself"""
        self.cmd('put backpack in backpack')
        assert not inside(self.backpack, self.backpack)

    def test_put_container_nested(self):
        """Try to put a container in a container"""
        self.cmd('put sphere in backpack')
        assert inside(self.sphere, self.backpack)
        self.cmd('put backpack in crate')
        assert inside(self.backpack, self.crate)
        self.cmd('get backpack from crate')
        self.cmd('drop backpack')
        self.cmd('get sphere from backpack')
        assert inside(self.sphere, self.player)

    def test_punch_damageable(self):
        """Damageables take damage when you punch them"""
        last_hp = self.backpack[Damageable].hp
        self.cmd('punch backpack')
        assert 'WHAP' in self.out
        assert self.backpack[Damageable].hp < last_hp

    def test_punch_self(self):
        """You take damage when you punch yourself"""
        last_hp = self.player[Damageable].hp
        self.cmd('punch self')
        assert 'WHAP' in self.out
        assert self.player[Damageable].hp < last_hp

    def test_destroy_container(self):
        """Containers drop their contents when destroyed"""
        self.cmd('get sphere')
        self.cmd('put sphere in backpack')
        self.flush()
        while self.backpack[Damageable].alive():
            self.cmd('punch backpack')
        assert not inside(self.sphere, self.backpack)
