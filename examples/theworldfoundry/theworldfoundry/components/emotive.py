from figment import Component

from theworldfoundry.components.spatial import Spatial, unique_selection
from theworldfoundry.modes import ActionMode


class Emotive(Component):
    """Enables an entity to emote."""


def emote(action_name, actor, verb, plural=None, join=None, selector=None):
    if not plural:
        plural = verb + "s"

    if not actor.is_([Spatial, Emotive]):
        actor.tell("You're unable to do that.")
        return

    if not selector:
        actor.Spatial.emit("{0.Named.Name} {1}.".format(actor, plural))
        actor.tell("You {0}.".format(verb))
        return

    targets = actor.Spatial.pick_nearby(selector)

    kwargs = {"selector": selector, "join": join}

    if not unique_selection(
        actor, action_name, "selector", selector, kwargs, targets, "nearby"
    ):
        return

    target = targets.pop()

    if join:
        actor.Spatial.emit(
            "{0.Named.Name} {1} {2} {3.Named.name}.".format(
                actor, plural, join, target
            ),
            exclude=target,
        )
        actor.tell("You {0} {1} {2.Named.name}.".format(verb, join, target))
        target.tell("{0.Named.Name} {1} {2} you.".format(actor, plural, join))
    else:
        actor.Spatial.emit(
            "{0.Named.Name} {1} {2.Named.name}.".format(actor, plural, target),
            exclude=target,
        )
        actor.tell("You {0} {1.Named.name}.".format(verb, target))
        target.tell("{0.Named.Name} {1} you.".format(actor, plural))


# These actions all need the same argument signature due to how
# `unique_selection` works.


@ActionMode.action(r"^dance(?: with (?P<selector>.+))?$")
def dance(actor, join=None, selector=None):
    return emote("dance", actor, "dance", join="with", selector=selector)


@ActionMode.action(r"^laugh(?: at (?P<selector>.+))?$")
def laugh(actor, join=None, selector=None):
    return emote("laugh", actor, "laugh", join="at", selector=selector)


@ActionMode.action(r"^lol$")
def lol(actor, join=None, selector=None):
    return emote("lol", actor, "laugh")


@ActionMode.action(r"^blink(?: at (?P<selector>.+))?$")
def blink(actor, join=None, selector=None):
    return emote("blink", actor, "blink", join="at", selector=selector)


@ActionMode.action(r"^frown(?: at (?P<selector>.+))?$")
def frown(actor, join=None, selector=None):
    return emote("frown", actor, "frown", join="at", selector=selector)


@ActionMode.action(r"^scowl(?: at (?P<selector>.+))?$")
def scowl(actor, join=None, selector=None):
    return emote("scowl", actor, "scowl", join="at", selector=selector)


@ActionMode.action(r"^eyebrow(?: at (?P<selector>.+))?$")
def eyebrow(actor, join=None, selector=None):
    return emote(
        "eyebrow",
        actor,
        "raise an eyebrow",
        "raises an eyebrow",
        join="at",
        selector=selector,
    )


@ActionMode.action(r"^shrug(?: at (?P<selector>.+))?$")
def shrug(actor, join=None, selector=None):
    return emote("shrug", actor, "shrug", join="at", selector=selector)


@ActionMode.action(r"^smile(?: at (?P<selector>.+))?$")
def smile(actor, join=None, selector=None):
    return emote("smile", actor, "smile", join="at", selector=selector)


@ActionMode.action(r"^grin(?: at (?P<selector>.+))?$")
def grin(actor, join=None, selector=None):
    return emote("grin", actor, "grin", join="at", selector=selector)


@ActionMode.action(r"^bow(?: to (?P<selector>.+))?$")
def bow(actor, join=None, selector=None):
    return emote("bow", actor, "bow", join="to", selector=selector)


@ActionMode.action(r"^nod(?: (?P<join>at|to) (?P<selector>.+))?$")
def nod(actor, join=None, selector=None):
    return emote("nod", actor, "nod", join=join, selector=selector)


@ActionMode.action(r"^cheer(?: for (?P<selector>.+))?$")
def cheer(actor, join=None, selector=None):
    return emote("cheer", actor, "cheer", join="for", selector=selector)


@ActionMode.action(r"^cough(?: (?P<join>on|at) (?P<selector>.+))?$")
def cough(actor, join=None, selector=None):
    return emote("cough", actor, "cough", join=join, selector=selector)


@ActionMode.action(r"^cry(?: on (?P<selector>.+))?$")
def cry(actor, join=None, selector=None):
    return emote("cry", actor, "cry", "cries", join="on", selector=selector)


@ActionMode.action(r"^point(?: (?P<join>to|at) (?P<selector>.+))?$")
def point(actor, join=None, selector=None):
    return emote("point", actor, "point", join=join, selector=selector)


@ActionMode.action(r"^wave(?: (?P<join>to|at) (?P<selector>.+))?$")
def wave(actor, join=None, selector=None):
    return emote("wave", actor, "wave", join=join, selector=selector)


@ActionMode.action(r"^wink(?: (?P<join>to|at) (?P<selector>.+))?$")
def wink(actor, join=None, selector=None):
    return emote("wink", actor, "wink", join=join, selector=selector)


@ActionMode.action(r"^poke (?P<selector>.+)$")
def poke(actor, selector, join=None):
    return emote("poke", actor, "poke", selector=selector)


@ActionMode.action(r"^hug (?P<selector>.+)$")
def hug(actor, selector, join=None):
    return emote("hug", actor, "hug", selector=selector)


@ActionMode.action(r"^kiss (?P<selector>.+)$")
def kiss(actor, selector, join=None):
    return emote("kiss", actor, "kiss", "kisses", selector=selector)
