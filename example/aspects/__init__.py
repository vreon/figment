from positioned import Positioned
from usable import Usable

### Override Event.witnesses

from schema import Event

# TODO
def find_witnesses(self):
    return set()

Event.witnesses = find_witnesses
