import sys
import os
import yaml
import tempfile
import shutil
# import zlib
import json

from schema import redis
from schema.entity import Entity


def fatal(message):
    print('Fatal: %s' % message)
    sys.exit(1)


class Zone(object):
    def __init__(self, id, config_path):
        self.id = id
        self.load_config(config_path)
        self.load_snapshot()

    def load_config(self, path):
        path = os.path.expanduser(path)

        try:
            with open(path) as f:
                config = yaml.safe_load(f)
        except EnvironmentError:
            fatal("couldn't read configuration file")
        except yaml.YAMLError as e:
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

        print('Loading entities from snapshot.')
        with open(self.snapshot_path, 'r') as f:
            snapshot = f.read()
            # if self.config['persistence'].get('compression'):
            #     snapshot = zlib.decompress(snapshot)
            snapshot = json.loads(snapshot)
            for entity_dict in snapshot['entities']:
                entity = Entity.from_dict(entity_dict)
                print('  [%s] %s' % (entity.id, entity.name))

        return True

    def save_snapshot(self):
        child_pid = os.fork()

        if not child_pid:
            f = tempfile.NamedTemporaryFile(delete=False)
            snapshot = json.dumps({
                'entities': [e.to_dict() for e in Entity.all()]
            })
            # if self.config['persistence'].get('compression'):
            #     snapshot = zlib.compress(snapshot)
            f.write(snapshot)
            f.close()
            shutil.move(f.name, self.snapshot_path)
            os._exit(os.EX_OK)

    def run(self):
        print('Listening.')
        try:
            while True:
                self.process_one_command()
        except Exception as e:
            print('Fatal: snapshotting and halting due to exception:')
            print(e)
        except BaseException as e:
            pass

        self.save_snapshot()

    def process_one_command(self):
        zone_key = 'zone:%s:incoming' % self.id
        queue_name, queue_item = redis.blpop([zone_key])

        entity_id, _, command = queue_item.partition(' ')

        # TODO: This is laughably insecure right now considering
        # that clients can specify the entity ID
        if entity_id == 'admin':
            print('[admin] %s' % command)
            if command == 'snapshot':
                self.save_snapshot()
            if command == 'crash':
                raise RuntimeError('Craaaaash')
            elif command == 'halt':
                sys.exit()
        else:
            entity = Entity.get(entity_id)

            if not entity:
                return

            print('[%s] <%s> %s' % (entity.id, entity.name, command))
            entity.perform(command)
