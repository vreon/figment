from schema import Aspect, action, jug

class Admin(Aspect):
    @staticmethod
    def validate(event):
        if not event.actor.has_aspect(Admin):
            event.actor.tell("You're unable to do that.")
            return

        event.trigger('before')
        return not event.prevented

    @action(r'^snapshot$')
    def snapshot(event):
        if Admin.validate(event):
            event.actor.tell('Saving snapshot.')
            event.actor.zone.save_snapshot()

    @action(r'^crash$')
    def crash(event):
        if Admin.validate(event):
            raise RuntimeError('Craaaaash')

    @action(r'^restart$')
    def restart(event):
        if Admin.validate(event):
            event.actor.tell('Restarting.')
            event.actor.zone.restart()

    @action(r'^halt$')
    def halt(event):
        if Admin.validate(event):
            event.actor.tell('Shutting down.')
            event.actor.zone.stop()

    @action(r'^ping$')
    def ping(event):
        if Admin.validate(event):
            event.actor.tell('Pong!')
