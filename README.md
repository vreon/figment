# Figment

A framework for creating multiplayer, text-based worlds.

## Installation

    $ pip install figment

## Usage

### Developing a world

API documentation is available in the docs directory -- or, at least, it will
be once the API is more stable!

### Running a server

Figment is more of a framework than an engine, and it doesn't make many
assumptions about your world, so there's not much to run out-of-the-box.

If you've already created a world (see figment-examples), ensure Redis is
running, then:

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
