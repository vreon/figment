from redis import StrictRedis
redis = StrictRedis()

from schema.logger import log
from schema.entity import Entity
from schema.aspect import Aspect, action, before, after
from schema.zone import Zone
from schema.event import Event
