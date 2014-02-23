import sys
import os
import tempfile
import shutil
# import zlib
import json
import traceback
from time import sleep

from redis import StrictRedis
from redis.connection import ConnectionError
from figment.entity import Entity
from figment.logger import log

def fatal(message):
    log.error('Fatal: %s' % message)
    sys.exit(1)


class Zone(object):
    def __init__(self):
        self.id = None
        self.entities = {}
        self.ticking_entities = set()
        self.tick_interval = 1
        self.running = False
        self.redis = None

    @classmethod
    def from_config(cls, id, config_path='config.json'):
        self = cls()

        self.id = id
        self.working_dir = '.'

        self.load_config(config_path)

        return self

    @property
    def tick_key(self):
        return 'zone:%s:tick' % self.id

    @property
    def incoming_key(self):
        return 'zone:%s:incoming' % self.id

    @property
    def import_key(self):
        return 'zone:%s:imports' % self.id

    def load_config(self, path):
        full_path = os.path.abspath(os.path.expanduser(path))

        try:
            with open(full_path) as f:
                config = json.loads(f.read())
        except EnvironmentError:
            fatal("couldn't read configuration file %s" % path)
        except ValueError as e:
            fatal("error in configuration file: %s" % e.message)

        if not self.id in config['zones']:
            fatal("undefined zone '%s'" % self.id)

        tick_interval = config['zones'][self.id].get('tick', 1)
        self.tick_interval = tick_interval

        # TODO: per-zone persistence settings

        persistence = config.get('persistence')
        if not persistence:
            fatal('unspecified persistence settings')

        # TODO: alternate persistence modes

        if not persistence['mode'] == 'snapshot':
            fatal("unrecognized persistence mode '%s'" % persistence['mode'])

        self.config = config
        self.working_dir = os.path.dirname(full_path)

        # TODO: Read redis connection params from config
        self.redis = StrictRedis()

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

    def load_components(self):
        # HACK: add basedir of the config file to the import path
        sys.path.append(self.working_dir)
        # As a side effect, Component.ALL gets populated with Component subclasses
        __import__('components')

    def start(self):
        try:
            self.redis.ping()
        except ConnectionError as e:
            fatal("Redis error: %s" % e.message)

        self.running = True
        log.info('Listening.')

        # Clear any existing tick events
        self.redis.ltrim(self.tick_key, 0, 0)
        try:
            while self.running:
                self.process_one_event()
        except Exception as e:
            log.error(traceback.format_exc())
        except BaseException as e:
            pass

        self.save_snapshot()

    def stop(self):
        self.running = False

    def start_ticker(self):
        log.info('Ticking every %ss.' % self.tick_interval)
        tock = False
        while True:
            log.debug('Tock.' if tock else 'Tick.')
            # TODO: timestamp here instead of True, for debugging?
            self.redis.rpush(self.tick_key, True)
            sleep(self.tick_interval)
            tock = not tock

    def listen(self, entity_id):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(Entity.messages_key_from_id(entity_id))
        for message in pubsub.listen():
            yield message['data']

    def process_one_event(self):
        key, value = self.redis.blpop([self.import_key, self.tick_key, self.incoming_key])

        if key == self.import_key:
            self.perform_import(json.loads(value))
        elif key == self.tick_key:
            self.perform_tick()
        else:
            entity_id, _, command = value.partition(' ')
            self.perform_command(entity_id, command)

    def enqueue_import(self, entities):
        if isinstance(entities, Entity):
            entities = [entities]
        self.redis.rpush(self.import_key, json.dumps([e.to_dict() for e in entities]))

    def enqueue_command(self, entity_id, command):
        self.redis.rpush(self.incoming_key, ' '.join([entity_id, command]))

    def perform_import(self, entity_dicts):
        # TODO: assumes entity IDs are globally unique
        for entity_dict in entity_dicts:
            Entity.from_dict(entity_dict, zone=self)

    def perform_command(self, entity_id, command):
        entity = self.get(entity_id)
        log.debug('Processing: <%s, %s> %s' % (entity.id, entity.name, command))
        entity.perform(command)

    def perform_tick(self):
        for entity in self.ticking_entities:
            # TODO: Somehow iterate over only ticking components
            for component in entity.components:
                if component.ticking:
                    component.tick()

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
