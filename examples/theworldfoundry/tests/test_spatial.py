import pytest

from theworldfoundry.modes import ActionMode

def test_move(player, courtyard):
    player.perform('go north')
    assert player.saw('Courtyard')

def test_move_invalid(player, courtyard):
    player.perform('go fish')
    assert player.saw('unable')

def test_move_sartre(player):
    player.perform('go north')
    assert player.saw("don't seem to be any exits")

def test_move_witness(player, statue, courtyard):
    player.perform('go north')
    assert statue.saw('Test Player travels north')

def test_say(player):
    player.perform('say Hello!')
    assert player.saw('Hello!')

def test_say_witness(player, statue, ghost):
    ghost.hearing = True
    statue.hearing = True
    statue.mode = ActionMode()

    player.perform('say Citizens! Hello!')
    assert player.saw('You say: "Citizens! Hello!"')
    assert statue.saw('Test Player says: "Citizens! Hello!"')
    assert ghost.saw('Test Player says: "Citizens! Hello!"')

    statue.perform('say Hello, orphan.')
    assert statue.saw('You say: "Hello, orphan."')
    assert player.saw('A statue says: "Hello, orphan."')
    assert ghost.saw('A statue says: "Hello, orphan."')

def test_sing_witness(player, statue):
    statue.hearing = True
    player.perform('sing The road goes ever on and on...')
    assert player.saw('You sing: "The road goes ever on and on..."')
    assert statue.saw('Test Player sings: "The road goes ever on and on..."')

@pytest.mark.xfail(reason='not implemented yet')
def test_whisper_to(player, statue, ghost):
    ghost.hearing = True
    statue.hearing = True

    player.perform('whisper to statue: Psst')
    assert player.saw('Psst')
    assert statue.saw('Psst')
    assert ghost.did_not_see('Psst')
