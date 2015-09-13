# Figment

A framework for creating multiplayer, text-based worlds.

## Installation

Figment will be available on PyPI when it is more stable. Until then, you can
install Figment directly from this repository with Pip:

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
  regions of the game at different tick speeds.

By extending Figment's base classes (particularly `Component` and `Mode`), you
define the vocabulary unique to your game world -- then construct your world's
people, places, and things using that vocabulary.

While your available vocabulary of Components and Modes cannot yet be changed
during runtime, they _can_ be dynamically applied to Entities (that's the whole
point, after all!) so you can even do a good chunk of worldbuilding from within
the game.

### Running a server

Figment is more of a framework than an engine, and it doesn't make many
assumptions about your world, so there's not much to run out-of-the-box.

If you've already created a world (see the `examples` directory for
inspiration), ensure Redis is running, then:

    $ cd /path/to/world
    $ figment run

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

## Background

Figment was created to explore the application of the entity-component-system
pattern to the realm of MUDs. It allows you, as a worldbuilder, to describe
components and attach them to entities to control how they behave and react.

When used properly, components can be very powerful. Imagine:

* Fire spreading to nearby objects with the Flammable component
* NPCs with the Vigilante component attacking thieves
* Armor with a Healing component that gradually restores health when worn
* Doors with a Breakable component that can be knocked down
* Switches that can only be weighed down by entities with the Heavy component

## License

Figment is made available under the terms of the Expat/MIT license. See LICENSE
for details.
