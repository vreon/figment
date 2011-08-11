import curses
import curses.textpad
from curses.wrapper import wrapper
from collections import deque
import time

from schema.entity import Entity
from schema.component import *

class Clock(object):
    """
    A simple rate-limiting object that ensures a function will be called at
    most every tick_length seconds.
    """
    def __init__(self, length=1, func=None):
        self.tick_length = length
        self.last_tick_time = 0
        self.funcs = []
        self.ticks = 0

    def register(self, func, *args, **kwargs):
        self.funcs.append((func, args, kwargs))

    def tick(self):
        now = time.time()
        should_tick = now - self.last_tick_time > self.tick_length
        if self.funcs and should_tick:
            self.ticks += 1
            self.last_tick_time = now
            for func, args, kwargs in self.funcs:
                func(*args, **kwargs)


class CursesUI(object):
    """
    A curses-based UI frontend to World.
    """
    def __init__(self, root_win, world):
        self.root_win = root_win
        self.world = world

        h, w = root_win.getmaxyx()
        self.content_win = curses.newwin(h - 1, w, 0, 0)
        self.prompt_win = curses.newwin(1, 2, h - 1, 0)
        self.input_win = curses.newwin(1, w - 2, h - 1, 2)
        self.input_pad = curses.textpad.Textbox(self.input_win)
        self.last_cmd = None

        # Enable auto-scrolling in the main window
        self.content_win.scrollok(1)
        self.content_win.idlok(1)

        self.set_prompt('>')

        # Make input non-blocking
        self.input_win.nodelay(1)

    def set_prompt(self, prompt_char):
        self.prompt_win.addstr(0, 0, prompt_char)
        self.prompt_win.noutrefresh()

        # Hack to move cursor back to input line
        self.input_win.noutrefresh()

    def display(self, value):
        self.content_win.addstr(value + '\n')
        self.content_win.noutrefresh()

        # Hack to move cursor back to input line
        self.input_win.noutrefresh()

    def run(self):
        while 1:
            raw_cmd = self._tick_until_command().strip()
            self.display(self._prompt_char() + ' ' + raw_cmd)

            split_cmd = raw_cmd.split()
            cmd, args = split_cmd[0], split_cmd[1:]

            if not cmd:
                continue

            # Meta-commands here
            if cmd == 'quit':
                break
            elif cmd == 'prompt':
                # Goofy debug command
                self.set_prompt(args[0] if len(args) else '>')
            elif cmd == '.':
                if not self.last_cmd:
                    continue
                self.world.command(self.last_cmd)
            else:
                # Let the world handle it
                self.last_cmd = raw_cmd
                self.world.command(raw_cmd)

    def _prompt_char(self):
        return self.prompt_win.instr(0, 0, 1)

    def _tick_until_command(self):
        """
        Blocks, ticking the world clock, until a command is entered.
        """
        while 1:
            if self._command_ready():
                cmd = self.input_pad.gather()
                self.input_win.erase()
                return cmd
            else:
                self.world.clock.tick()
                self._update_windows()
                curses.doupdate()

    def _command_ready(self):
        ch = self.input_win.getch()
        return ch != -1 and not self.input_pad.do_command(ch)

    def _update_windows(self):
        while self.world.output:
            self.display(self.world.output.popleft())


class World(object):
    def __init__(self):
        self.clock = Clock()
        self.output = deque()
        self.entities = []

        self.player = None

        # TODO: Don't create player here
        # TODO: Load all of this from a file

        self.player = Entity('self', 'Yep, that\'s you.')
        self.player.is_now(Positionable, 0, 0)
        self.player.is_now(Massive, 75)
        self.player.is_now(Damageable)
        self.player[Damageable].scale[Damageable.DamageType.ELECTRICAL] = 1.0
        self.player.is_now(Flammable)
        self.player.is_now(Soakable)
        self.player.is_now(Voluminous, 8000)
        self.player.is_now(Container, 5000, 20)

        self.entities.append(self.player)

        self.clock.register(self.tick)

        self.render('Welcome to the world.')
        self.render('Type commands below to play.')

    def tick(self):
        for ent in self.entities:
            ent.tick()

    def render(self, value):
        self.output.append(value)

    def _ents_near(self, ent, radius=30):
        return [e for e in self.entities if e.is_(Positionable) and e[Positionable].distance_from(ent) <= radius]

    def _get_nearby_ent(self, args, check_inventory=True):
        ent_set = self._ents_near(self.player)
        if check_inventory and self.player.is_(Container):
            ent_set = self.player[Container].contents + ent_set
        return self._get_ent_from_set(ent_set, args, area='nearby')

    def _get_ent_from_set(self, ent_set, args, area='in that area'):
        # If the user supplied an ent ID, remove it from the name
        ent_id = None
        try:
            ent_id = int(args[-1])
            args.pop()
        except ValueError:
            pass

        name = ' '.join(args)

        if name in ('self', 'me', 'myself'):
            return self.player

        matching_ents = [ent for ent in ent_set if name in ent.name and not ent.id == self.player.id]
        num_matched = len(matching_ents)
        if num_matched == 0:
            self.render('There\'s no {} {}.'.format(name, area))
            return None
        elif num_matched == 1:
            return matching_ents[0]
        elif ent_id:
            if name:
                # Specified name and ent_id, e.g. "get hat 2"
                for ent in matching_ents:
                    if ent.id == ent_id:
                        return ent
                self.render('There\'s no {} {} with the ID {}.'.format(name, area, ent_id))
                return None
            else:
                # Specified ent_id only, e.g. "get 2"
                for ent in ent_set:
                    if ent.id == ent_id and not ent.id == self.player.id:
                        return ent
                self.render('There\'s nothing {} with the ID {}.'.format(area, ent_id))
                return None
        else:
            self.render('Which {} do you mean?'.format(name))
            for ent in matching_ents:
                self.render('    {} ({})'.format(ent.name, ent.id))

    def _try_to_store(self, ent, container_ent):
        result = container_ent[Container].store(ent)
        if result == Container.Result.UNSTORABLE:
            self.render('You can\'t take the {}.'.format(ent.name))
            return False
        elif result == Container.Result.ALREADY_STORED:
            self.render('You need to take the {} out of the {} first.'.format(ent.name, ent[Storable].container.name))
            return False
        elif result == Container.Result.TOO_BIG:
            self.render('The {} won\'t fit.'.format(ent.name))
            return False
        elif result == Container.Result.TOO_HEAVY:
            self.render('The {} is too heavy.'.format(ent.name))
            return False
        return True

    def cmd_examine(self, args):
        if not args:
            self.render('Examine what?')
            return

        ent = self._get_nearby_ent(args)

        if not ent:
            return

        self.render(str(ent))

    def cmd_look(self, args):
        # Look at everything nearby
        if not args:
            ents_nearby = self._ents_near(self.player)
            if not ents_nearby:
                self.render('There\'s nothing interesting nearby.')
                return

            self.render('Things nearby:')
            for ent in ents_nearby:
                self.render('    ' + ent.name)
            return

        # Look inside a particular object
        if args[0] in ('in', 'inside', 'into'):
            args.pop(0)

            ent = self._get_nearby_ent(args)
            if not ent:
                return

            if not ent.is_(Container):
                self.render('You can\'t look inside of that.')
                return

            self.render('Contents:')
            if ent[Container].contents:
                for item in ent[Container].contents:
                    self.render('    ' + item.name)
            else:
                self.render('    nothing')
            return

        # Look at a particular object
        if args[0] in ('at',):
            args.pop(0)

        ent = self._get_nearby_ent(args)
        if not ent:
            return

        self.render(ent.desc)

    def cmd_inventory(self, args):
        self.cmd_look('in self'.split())

    def cmd_get(self, args):
        # TODO: This shares a lot of logic with "put"
        if not self.player.is_(Container):
            self.render('You\'re unable to hold items at the moment.')
            return

        # Target nearby entities if a container wasn't specified
        if not 'from' in args:
            ent = self._get_nearby_ent(args, check_inventory=False)
            if not ent:
                return

            if ent.id == self.player.id:
                self.render('You can\'t put yourself in your inventory.')
                return

            if self._try_to_store(ent, self.player):
                self.render('You pick up the {}.'.format(ent.name))
            return

        index = args.index('from')

        target_ent_name = args[:index]
        if not target_ent_name:
            self.render('Get what?')
            return

        container_name = args[index + 1:]
        if not container_name:
            self.render('Get it from what?')
            return

        container_ent = self._get_nearby_ent(container_name)
        if not container_ent:
            return

        if container_ent.id == self.player.id:
            self.render('You can\'t get things from your inventory, they\'d just go right back in!')
            return

        if not container_ent.is_(Container):
            self.render('That {} can\'t hold items.'.format(container_ent.name))
            return

        ent = self._get_ent_from_set(
            container_ent[Container].contents,
            target_ent_name,
            area='in the {}'.format(container_ent.name)
        )

        if not ent:
            return

        if ent.id == self.player.id:
            self.render('You can\'t put yourself in your inventory.')
            return

        container_ent[Container].remove(ent)
        if self._try_to_store(ent, self.player):
            self.render('You take the {} from the {}.'.format(ent.name, container_ent.name))
        else:
            container_ent[Container].store(ent)

    def cmd_take(self, args):
        self.cmd_get(args)

    def cmd_remove(self, args):
        self.cmd_get(args)

    def cmd_pick(self, args):
        # This is kind of a hack :p
        if args[0] == 'up':
            args.pop(0)
        self.cmd_get(args)

    def cmd_drop(self, args):
        if not self.player.is_(Container):
            self.render('You can\'t carry items at the moment, so there\'s nothing to drop.')
            return

        inventory = self.player[Container].contents
        ent = self._get_ent_from_set(inventory, args, 'in your inventory')

        if not ent:
            return

        if self.player[Container].remove(ent):
            self.render('You drop the {}.'.format(ent.name))
        else:
            self.render('You\'re unable to drop the {}.'.format(ent.name))

    def cmd_put(self, args):
        # TODO: This shares a lot of logic with "get"
        if not self.player.is_(Container):
            self.render('You\'re unable to put items at the moment.')
            return

        if not 'in' in args:
            self.render('Put {} in what?'.format(' '.join(args)))
            return

        index = args.index('in')

        target_ent_name = args[:index]
        if not target_ent_name:
            self.render('Put what?')
            return

        container_name = args[index + 1:]
        if not container_name:
            self.render('Put it in what?')
            return

        container_ent = self._get_nearby_ent(container_name)
        if not container_ent:
            return

        if container_ent.id == self.player.id:
            self.cmd_get(target_ent_name)
            return

        if not container_ent.is_(Container):
            self.render('That {} can\'t hold items.'.format(container_ent.name))
            return

        ent = self._get_nearby_ent(target_ent_name)

        if not ent:
            return

        if ent.id == self.player.id:
            self.render('You can\'t put yourself in that (because it\'s not implemented yet).')
            return

        if ent.id == container_ent.id:
            self.render('You can\'t store something in itself.')
            return

        self.player[Container].remove(ent)
        if self._try_to_store(ent, container_ent):
            self.render('You put the {} in the {}.'.format(ent.name, container_ent.name))
        else:
            self.player[Container].store(ent)

    def cmd_punch(self, args):
        if not args:
            self.render('Punch what?')
            return

        ent = self._get_nearby_ent(args)

        if not ent:
            return

        self.render('** WHAP **')
        if ent.id == self.player.id:
            self.render('You punched yourself in the face!!')
            dmg = self.player[Damageable].damage(Damageable.DamageType.PHYSICAL, 5)
            self.render('You took {} damage.'.format(dmg))
        else:
            self.render('You punch the {}.'.format(ent.name))
            dmg = ent[Damageable].damage(Damageable.DamageType.PHYSICAL, 5)
            self.render('The {} took {} damage.'.format(ent.name, dmg))

    def cmd_time(self, args):
        self.render('World time is {}.'.format(self.clock.ticks))

    def command(self, raw_cmd):
        # TODO: getattr here is kind of hokey, maintain a dict of commands
        #       instead so we can enumerate them on 'help'
        split_cmd = raw_cmd.strip().split()
        cmd, args = split_cmd[0], split_cmd[1:]
        if hasattr(self, 'cmd_' + cmd):
            getattr(self, 'cmd_' + cmd)(args)
        else:
            self.render('You can\'t do that.')

def _main(stdscr):
    world = World()
    ui = CursesUI(stdscr, world)
    ui.run()

def play():
    try:
        curses.wrapper(_main)
    except KeyboardInterrupt:
        pass
