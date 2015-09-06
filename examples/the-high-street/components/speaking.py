from figment import Component


class Speaking(Component):
    @action(r'^speak(?: to)? (?P<selector>.+)$')
    def speak_to(event):
        if not event.actor.has_component(Position):
            event.actor.tell("You're unable to do that.")
            return

        event.target = event.actor.Position.pick_nearby(event.selector)
        if not event.target:
            return

        if not event.target.has_component(Speaking):
            event.actor.tell("{0.Name} doesn't seem very talkative at the moment.")
            return

        event.actor.tell("{0.Name} doesn't seem very talkative at the moment.")
