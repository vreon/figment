import logging
from termcolor import colored

FORMAT = '%(asctime)s %(levelname)-8s %(message)s'
DATE_FORMAT = '%m-%d %H:%M:%S'

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'white',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    }

    @classmethod
    def _level_color(cls, record, string):
        return colored(string, cls.COLORS.get(record.levelname, 'white'), attrs=['bold'])

    def format(self, record):
        super(ColoredFormatter, self).format(record)
        # TODO: Don't color if the stream istty
        return ' '.join([
            str(record.asctime),
            self._level_color(record, '%8s' % record.levelname),
            str(record.message),
        ])

def create_logger():
    log = logging.getLogger('schema')
    log.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter(fmt=FORMAT, datefmt=DATE_FORMAT))
    log.addHandler(handler)

    return log

log = create_logger()
