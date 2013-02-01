from positioned import Positioned
from usable import Usable
from dark import Dark

### Override Event.witnesses

from schema import Event, Entity

# TODO: Restrict this
def find_witnesses(self):
    return Entity.ALL.values()

Event.witnesses = find_witnesses
