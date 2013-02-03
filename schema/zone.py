import sys
import os
import tempfile
import shutil
# import zlib
import json
import traceback

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

    @classmethod
    def from_disk(cls, id, config_path='config.json'):
        self = cls()

        self.id = id
        self.working_dir = '.'

        self.load_config(config_path)
        self.load_aspects()
        self.load_snapshot()

        return self

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
                entity = Entity.from_dict(entity_dict)
                entity.zone = self

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
                self.process_one_command()
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

    def process_one_command(self):
        zone_key = 'zone:%s:incoming' % self.id
        queue_name, queue_item = redis.blpop([zone_key])

        entity_id, _, command = queue_item.partition(' ')
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
