import sys
import os
import tempfile
import shutil

# import zlib
import traceback
import importlib
import inspect
from time import sleep

from redis import Redis
from redis.connection import ConnectionError
from figment.component import Component
from figment.mode import Mode
from figment.entity import Entity
from figment.logger import log
from figment.serializers import SERIALIZERS
from figment.debug import DefaultRenderer


def fatal(message):
    log.critical(message)
    sys.exit(1)


class Zone:
    def __init__(self):
        self.id = None
        self.world_path = ""
        self.entities = {}
        self.components = {}
        self.renderer_class = DefaultRenderer
        self.entities_by_component_name = {}
        self.ticking_entities = set()
        self.tick_interval = 1
        self.running = False
        self.redis = None
        self._max_id = 0

    @classmethod
    def from_config(cls, id, world_path):
        self = cls()

        self.id = id
        self.world_path = world_path

        self.load_config()

        return self

    @property
    def tick_key(self):
        return "zone:%s:tick" % self.id

    @property
    def incoming_key(self):
        return "zone:%s:incoming" % self.id

    @staticmethod
    def messages_key(entity_id):
        return "entity:%s:messages" % entity_id

    def next_id(self):
        self._max_id += 1
        return self._max_id

    def load_config(self):
        base_path = os.path.abspath(os.path.expanduser(self.world_path))

        config = None

        for serializer in SERIALIZERS.values():
            config_filename = "config.%s" % serializer.extension
            config_path = os.path.join(base_path, config_filename)

            try:
                with open(config_path) as f:
                    config = serializer.unserialize(f.read())
            except EnvironmentError:
                continue
            except Exception as e:  # TODO: UnserializeError
                fatal("Error while reading %s: %s" % (config_path, e))

        if config is None:
            fatal(
                "Unable to read config.{%s} from %s"
                % (",".join(s.extension for s in SERIALIZERS.values()), base_path)
            )

        if self.id not in config["zones"]:
            fatal("Undefined zone '%s'" % self.id)

        tick_interval = config["zones"][self.id].get("tick", 1)
        self.tick_interval = tick_interval

        # TODO: per-zone persistence settings

        persistence = config.get("persistence")
        if not persistence:
            fatal("Unspecified persistence settings")

        # TODO: alternate persistence modes

        if not persistence["mode"] == "snapshot":
            fatal("Unrecognized persistence mode '%s'" % persistence["mode"])

        self.config = config

        self.redis = Redis(config["redis"]["host"], config["redis"]["port"])

        renderer_name = self.config["world"].get("renderer")
        if renderer_name:
            renderer_module_name, _, renderer_class_name = renderer_name.rpartition(".")
            renderer_module = importlib.import_module(renderer_module_name)
            self.renderer_class = getattr(renderer_module, renderer_class_name)

    @property
    def snapshot_path(self):
        snapshot_path = self.config["persistence"]["file"]
        try:
            snapshot_path = snapshot_path.format(id=self.id)
        except TypeError:
            pass
        return os.path.join(self.world_path, os.path.expanduser(snapshot_path))

    @property
    def snapshot_serializer(self):
        extension = self.config["persistence"].get("format")
        if not extension:
            extension = os.path.splitext(self.snapshot_path)[1][1:]
        return SERIALIZERS[extension]

    def load_snapshot(self):
        if not os.path.exists(self.snapshot_path):
            return False

        log.info("Loading snapshot: %s" % self.snapshot_path)
        with open(self.snapshot_path, "r") as f:
            snapshot = f.read()
            # if self.config['persistence'].get('compressed'):
            #     snapshot = zlib.decompress(snapshot)
            snapshot = self.snapshot_serializer.unserialize(snapshot)

            log.info("Creating entities...")

            for entity_dict in snapshot["entities"]:
                entity = Entity.from_dict(
                    {"id": entity_dict["id"], "hearing": entity_dict["hearing"]}, self
                )
                self._max_id = max(self._max_id, entity.id)

            log.info("Creating components...")

            for entity_dict in snapshot["entities"]:
                entity = self.get(entity_dict["id"])
                entity.attach_from_dict(entity_dict)

        return True

    def save_snapshot(self):
        log.info("Saving snapshot: %s" % self.snapshot_path)
        child_pid = os.fork()

        if not child_pid:
            f = tempfile.NamedTemporaryFile(delete=False)
            snapshot = self.snapshot_serializer.serialize(
                {"entities": [e.to_dict() for e in self.all()]}
            )
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

        self.components = self._import_subclasses(
            self.config["world"]["components"], Component
        )
        self.modes = self._import_subclasses(self.config["world"]["modes"], Mode)

        log.debug(
            "Loaded %s component(s) and %s mode(s)."
            % (len(self.components), len(self.modes))
        )

    def start(self):
        try:
            self.redis.ping()
        except ConnectionError as e:
            fatal("Redis error: %s" % e.message)

        self.running = True
        log.info("Listening.")

        # Clear any existing tick events
        self.redis.ltrim(self.tick_key, 0, 0)
        try:
            while self.running:
                self.process_one_event()
        except Exception as e:
            log.critical(traceback.format_exc())
        except BaseException as e:
            pass
        finally:
            self.save_snapshot()

    def stop(self):
        self.running = False

    def start_ticker(self):
        log.info("Ticking every %ss." % self.tick_interval)
        tock = False
        while True:
            log.debug("Tock." if tock else "Tick.")
            # TODO: timestamp here instead of 1, for debugging?
            self.redis.rpush(self.tick_key, 1)
            sleep(self.tick_interval)
            tock = not tock

    def send_message(self, entity_id, message):
        self.redis.publish(self.messages_key(entity_id), message)

    def listen(self, entity_id):
        subscription = self.subscribe(entity_id)
        for message in subscription.listen():
            yield message["data"]

    # TODO: Leaky abstraction :\
    def subscribe(self, entity_id):
        subscription = self.redis.pubsub(ignore_subscribe_messages=True)
        subscription.subscribe(self.messages_key(entity_id))
        return subscription

    def process_one_event(self):
        key, value = self.redis.blpop([self.tick_key, self.incoming_key])

        if key.decode("utf-8") == self.tick_key:
            self.perform_tick()
        else:
            entity_id, _, command = value.decode("utf-8").partition(" ")
            self.perform_command(int(entity_id), command)

    def enqueue_command(self, entity_id, command):
        self.redis.rpush(self.incoming_key, " ".join([str(entity_id), command]))

    def perform_command(self, entity_id, command):
        entity = self.get(entity_id)
        log.debug("Processing: [%s] %s" % (entity.id, command))
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

    def find(self, component_name):
        if inspect.isclass(component_name):
            component_name = component_name.__name__
        return self.entities_by_component_name.get(component_name, set())

    def spawn(self, components=[], **kwargs):
        entity = Entity(**kwargs)
        self.add(entity)
        if components:
            entity.components.add(components)
        return entity

    def clone(self, entity):
        # TODO FIXME: This is fairly awful
        return Entity.from_dict(entity.to_dict(), self)

    def destroy(self, entity):
        entity.components.purge()
        self.remove(entity)

    def add(self, entity):
        entity.id = self.next_id()
        entity.zone = self
        self.entities[entity.id] = entity

    def remove(self, entity):
        self.entities.pop(entity.id)
        entity.zone = None
