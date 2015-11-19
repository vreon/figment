# The World Foundry

An example game set at a fictitious university devoted to the craft of creating Figment worlds.

## Components

This world includes several components that can be reused or adapted for your own purposes.

- **Spatial** is responsible for describing the spatial (hierarchical) relationship between entities. It handles much of the core functionality you'd expect from a MUD related to moving around, looking at, taking and dropping things, and emitting messages to "nearby" entities.
- **Dark** modifies the typical behavior of `look` for some entities.
- **Emotive** allows entities to emit a textual description of them performing an action, much like the `/me` command would on IRC.
- **Important** prevents an entity from being dropped or taken.
- **Sticky** is a silly example of an entity that will randomly fail to be dropped.
- **Wandering** entities will meander randomly between the specified rooms.
