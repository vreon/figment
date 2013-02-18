from schema import Aspect


class Speaking(Aspect):
    @action(r'^speak(?: to)? (?P<descriptor>.+)$')
    def speak_to(event):
        if not event.actor.has_aspect(Positioned):
            event.actor.tell("You're unable to do that.")
            return

        event.target = event.actor.Positioned.pick_nearby(event.descriptor)
        if not event.target:
            return

        if not event.target.has_aspect(Speaking):
            event.actor.tell("{0.Name} doesn't seem very talkative at the moment.")
            return

        yield 'before'
        if event.prevented:
            return

        event.actor.tell("{0.Name} doesn't seem very talkative at the moment.")
