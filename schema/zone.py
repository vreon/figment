import sys
import os
import tempfile
import shutil
# import zlib
import json
import traceback
from time import sleep

from schema import redis
from schema.entity import Entity
from schema.logger import log


def fatal(message):
    log.error('Fatal: %s' % message)
    sys.exit(1)


class Zone(object):
    def __init__(self):
        self.id = None
        self.entities = {}
        self.ticking = set()
        self.tick_every = 1

    @classmethod
    def from_config(cls, id, config_path='config.json'):
        self = cls()

        self.id = id
        self.working_dir = '.'

        self.load_config(config_path)
        self.load_aspects()

        return self

    @property
    def tick_key(self):
        return 'zone:%s:tick' % self.id

    @property
    def incoming_key(self):
        return 'zone:%s:incoming' % self.id

    def load_config(self, path):
        path = os.path.abspath(os.path.expanduser(path))

        try:
            with open(path) as f:
                config = json.loads(f.read())
        except EnvironmentError:
            fatal("couldn't read configuration file")
        except ValueError as e:
            fatal("error in configuration file:\n%s" % e)

        if not self.id in config['zones']:
            fatal("undefined zone '%s'" % self.id)

        tick_every = config['zones'][self.id].get('tick', 1)
        self.tick_every = tick_every

        # TODO: per-zone persistence settings

        persistence = config.get('persistence')
        if not persistence:
            fatal('unspecified persistence settings')

        # TODO: alternate persistence modes

        if not persistence['mode'] == 'snapshot':
            fatal("unrecognized persistence mode '%s'" % persistence['mode'])

        self.config = config
        self.working_dir = os.path.dirname(path)

    @property
    def snapshot_path(self):
        snapshot_path = self.config['persistence']['file']
        try:
            snapshot_path = snapshot_path % self.id
        except TypeError:
            pass
        return os.path.expanduser(snapshot_path)

    def load_snapshot(self):
        if not os.path.exists(self.snapshot_path):
            return False

        log.info('Loading entities from snapshot.')
        with open(self.snapshot_path, 'r') as f:
            snapshot = f.read()
            # if self.config['persistence'].get('compressed'):
            #     snapshot = zlib.decompress(snapshot)
            snapshot = json.loads(snapshot)
            for entity_dict in snapshot['entities']:
                entity = Entity.from_dict(entity_dict, zone=self)

        return True

    def save_snapshot(self):
        log.info('Saving snapshot: %s' % self.snapshot_path)
        child_pid = os.fork()

        if not child_pid:
            f = tempfile.NamedTemporaryFile(delete=False)
            snapshot = json.dumps({
                'entities': [e.to_dict() for e in self.all()]
            })
            # if self.config['persistence'].get('compressed'):
            #     snapshot = zlib.compress(snapshot)
            f.write(snapshot)
            f.close()
            shutil.move(f.name, self.snapshot_path)
            os._exit(os.EX_OK)

    def load_aspects(self):
        # HACK: add basedir of the config file to the import path
        sys.path.append(self.working_dir)
        # As a side effect, Aspect.ALL gets populated with Aspect subclasses
        __import__(self.config.get('aspects', {}).get('path', 'aspects'))

    def start(self):
        log.info('Listening.')
        try:
            while True:
                self.process_one_event()
        except Exception as e:
            log.error(traceback.format_exc())
        except BaseException as e:
            pass

        self.save_snapshot()

    def restart(self):
        # TODO: Make sure this actually works
        log.info('Restarting.')
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def stop(self):
        # TODO: Is this necessary?
        # Couldn't we just fall out of the event loop?
        sys.exit()

    def start_ticker(self):
        log.info('Ticking.')
        while True:
            log.debug('Tick.')
            # TODO: timestamp here instead of True, for debugging?
            redis.rpush(self.tick_key, True)
            sleep(self.tick_every)

    def tick(self):
        for entity in self.ticking:
            # TODO: Somehow iterate over only ticking aspects
            for aspect in entity.aspects:
                if aspect.ticking:
                    aspect.tick()

    def process_one_event(self):
        key, queue_item = redis.blpop([self.tick_key, self.incoming_key])

        if key == self.tick_key:
            self.tick()
        else:
            entity_id, _, command = queue_item.partition(' ')
            self.perform(entity_id, command)

    def perform(self, entity_id, command):
        entity = self.get(entity_id)

        if not entity:
            return

        log.debug('Processing: <%s, %s> %s' % (entity.id, entity.name, command))
        entity.perform(command)

    # Entity helpers

    def get(self, id):
        return self.entities.get(id)

    def all(self):
        return self.entities.values()

    def purge(self):
        log.info('Purging all entities.')
        # TODO: Modifies the dict while iterating; is this ok?
        for entity in self.entities.values():
            entity.destroy()
