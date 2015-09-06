import sys
import os
import tempfile
import shutil
# import zlib
import json
import traceback
import importlib
import inspect
from time import sleep

from redis import StrictRedis
from redis.connection import ConnectionError
from figment.component import Component
from figment.modes import Mode
from figment.entity import Entity
from figment.logger import log
from figment.serializers import SERIALIZERS


def fatal(message):
    log.critical(message)
    sys.exit(1)


class Zone(object):
    def __init__(self):
        self.id = None
        self.world_path = ''
        self.entities = {}
        self.components = {}
        self.ticking_entities = set()
        self.tick_interval = 1
        self.running = False
        self.redis = None

    @classmethod
    def from_config(cls, id, world_path):
        self = cls()

        self.id = id
        self.world_path = world_path

        self.load_config()

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

    def load_config(self):
        base_path = os.path.abspath(os.path.expanduser(self.world_path))

        config = None

        for serializer in SERIALIZERS.values():
            config_filename = 'config.%s' % serializer.extension
            config_path = os.path.join(base_path, config_filename)

            try:
                with open(config_path) as f:
                    config = serializer.unserialize(f.read())
            except EnvironmentError:
                continue
            except Exception as e:  # TODO: UnserializeError
                fatal('Error while reading %s: %s' % (config_path, e))

        if config is None:
            fatal('Unable to read config.{%s} from %s' % (
                ','.join(s.extension for s in SERIALIZERS.values()), base_path
            ))

        if not self.id in config['zones']:
            fatal("Undefined zone '%s'" % self.id)

        tick_interval = config['zones'][self.id].get('tick', 1)
        self.tick_interval = tick_interval

        # TODO: per-zone persistence settings

        persistence = config.get('persistence')
        if not persistence:
            fatal('Unspecified persistence settings')

        # TODO: alternate persistence modes

        if not persistence['mode'] == 'snapshot':
            fatal("Unrecognized persistence mode '%s'" % persistence['mode'])

        self.config = config

        self.redis = StrictRedis(
            config['redis']['host'],
            config['redis']['port'],
        )

    @property
    def snapshot_path(self):
        snapshot_path = self.config['persistence']['file']
        try:
            snapshot_path = snapshot_path.format(id=self.id)
        except TypeError:
            pass
        return os.path.join(
            self.world_path,
            os.path.expanduser(snapshot_path)
        )

    @property
    def snapshot_serializer(self):
        extension = self.config['persistence'].get('format')
        if not extension:
            extension = os.path.splitext(self.snapshot_path)[1][1:]
        return SERIALIZERS[extension]

    def load_snapshot(self):
        if not os.path.exists(self.snapshot_path):
            return False

        log.info('Loading snapshot: %s' % self.snapshot_path)
        with open(self.snapshot_path, 'r') as f:
            snapshot = f.read()
            # if self.config['persistence'].get('compressed'):
            #     snapshot = zlib.decompress(snapshot)
            snapshot = self.snapshot_serializer.unserialize(snapshot)
            for entity_dict in snapshot['entities']:
                entity = Entity.from_dict(entity_dict, self)

        return True

    def save_snapshot(self):
        log.info('Saving snapshot: %s' % self.snapshot_path)
        child_pid = os.fork()

        if not child_pid:
            f = tempfile.NamedTemporaryFile(delete=False)
            snapshot = self.snapshot_serializer.serialize({
                'entities': [e.to_dict() for e in self.all()]
            })
            # if self.config['persistence'].get('compressed'):
            #     snapshot = zlib.compress(snapshot)
            f.write(snapshot)
            f.close()
            shutil.move(f.name, self.snapshot_path)
            os._exit(os.EX_OK)

    def _import_subclasses(self, module_name, parent_class):
        module = importlib.import_module(module_name)
        return {
            cls.__name__: cls
            for name, cls in inspect.getmembers(module)
            if inspect.isclass(cls) and issubclass(cls, parent_class)
        }

    def load_modules(self):
        sys.path.append(self.world_path)

        self.components = self._import_subclasses('components', Component)
        self.modes = self._import_subclasses('modes', Mode)

        log.debug('Loaded %s component(s) and %s mode(s).' % (
            len(self.components), len(self.modes)
        ))

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
            log.critical(traceback.format_exc())
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
            Entity.from_dict(entity_dict, self)

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

    def spawn(self, *args, **kwargs):
        kwargs['zone'] = self
        return Entity(*args, **kwargs)

    def purge(self):
        log.info('Purging all entities.')
        # TODO: Modifies the dict while iterating; is this ok?
        for entity in self.entities.values():
            entity.destroy()
