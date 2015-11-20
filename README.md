# Figment

Figment is a framework for creating multiplayer, text-based worlds. It was
originally designed to explore the application of the "entity-component-system"
architectural pattern to the realm of MUDs.

## Philosophy

Components, as Figment defines them, are little chunks of behavior that can be
attached to any Entity. Composability is a powerful pattern, and Components are
no exception. Here are some ways you can use them:

* Fire that spreads to nearby entities with the Flammable Component
* NPCs with a Vigilante Component who will attack criminals on sight
* Armor with a Healing Component that gradually restores health when worn
* Doors with a Breakable Component that can be knocked down
* Switches that can only be weighed down by entities with the Heavy Component

Figment is explicitly designed to empower worldbuilders to create dynamic
environments populated by entities that interact with each other in intricate
(and even unexpected) ways, so: experiment and have fun!

## Installation

Figment is under active development. You can install it from PyPI:

    $ pip install figment

Or directly from this repository (recommended, for now):

    $ pip install git+git://github.com/vreon/figment.git

## Usage

### Developing a world

To create a world, you'll need to familiarize yourself with some terminology:

* An **Entity** is any thing that exists within your world. It doesn't need to
  be physical or tangible.  
  *Examples*: a sword, a room, a monster spawner, a player
* A **Component** is like an adjective that can be attached to an Entity to
  change its behavior and how other Entities behave toward it.  
  *Examples*: a Component to describe the Entity's location in space, a
  Component that causes the Entity to meander automatically from room to room,
  a Component that allows the Entity to use worldbuilding commands
* A **Mode** is the lens through which a textual command, like "go north", is
  interpreted. An Entity has one Mode at any given time (or zero if it has no
  agency). Commands issued by an Entity are passed through that Entity's Mode,
  and the Mode is then responsible for updating the state of the world and
  sending messages to any affected Entities.  
  *Examples*: an action Mode for moving around within the world, a conversation
  Mode for talking to NPCs, a setup Mode for character creation
* A **Zone** is a slice of a world. It acts like an isolated space for a group
  of Entities. You can use Zones as server shards or to run different logical
  regions of the world at different tick speeds.

By extending Figment's base classes (particularly `Component` and `Mode`), you
define the vocabulary unique to your world -- then construct your world's
people, places, and things using that vocabulary.

While your available vocabulary of Components and Modes cannot yet be changed
during runtime, they _can_ be dynamically applied to Entities (that's the whole
point, after all!) so you can even do a good chunk of worldbuilding from within
the world itself if you build the appropriate tools.

Consult the example worlds to get an idea of how to structure yours.

### Running a server

Figment is more of a framework than an engine, and it doesn't make many
assumptions about your world, so there's not much to run out-of-the-box.

If you have already created a world, or would like to run one of the examples:

    $ cd /path/to/world
    $ figment run

(Make sure that the Redis instance referenced in your world's config is
accessible from this host.)

If the world contains ticking components, you'll also need to run a ticker:

    $ figment run -t

### Running a client

Presently, Figment clients must communicate directly with the backing Redis
instance. This is obviously insecure, so it's strongly recommended to write a
client that can act as an intermediary between Redis and whatever protocol you
want to support (Websockets, IRC, Telnet, etc). Eventually, Figment will
provide plugins for the most common client protocols.

For now, assuming you have direct access to Redis, you can use the Figment CLI
to spy on the message stream received by an entity, and to interactively issue
commands as an entity. Using both of these streams simultaneously (in separate
windows or a terminal multiplexer) results in a makeshift client:

    $ figment listen entity_id
    $ figment prompt entity_id

## License

Figment is made available under the terms of the Expat/MIT license. See LICENSE
for details.
