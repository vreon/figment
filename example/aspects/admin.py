from schema import Aspect, action

class Admin(Aspect):
    @action(r'^snapshot$')
    def snapshot(event):
        if not event.actor.has_aspect(Admin):
            event.actor.tell("You're unable to do that.")
            return

        yield 'before'
        if not event.prevented:
            event.actor.tell('Saving snapshot.')
            event.actor.zone.save_snapshot()

    @action(r'^crash$')
    def crash(event):
        if not event.actor.has_aspect(Admin):
            event.actor.tell("You're unable to do that.")
            return

        yield 'before'
        if not event.prevented:
            raise RuntimeError('Craaaaash')

    @action(r'^(restart|reload)$')
    def restart(event):
        if not event.actor.has_aspect(Admin):
            event.actor.tell("You're unable to do that.")
            return

        yield 'before'
        if not event.prevented:
            event.actor.tell('Restarting.')
            event.actor.zone.restart()

    @action(r'^halt$')
    def halt(event):
        if not event.actor.has_aspect(Admin):
            event.actor.tell("You're unable to do that.")
            return

        yield 'before'
        if not event.prevented:
            event.actor.tell('Shutting down.')
            event.actor.zone.stop()

    @action(r'^ping$')
    def ping(event):
        if not event.actor.has_aspect(Admin):
            event.actor.tell("You're unable to do that.")
            return

        yield 'before'
        if not event.prevented:
            event.actor.tell('Pong!')
