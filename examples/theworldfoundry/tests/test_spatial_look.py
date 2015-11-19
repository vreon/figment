from theworldfoundry.components import Dark

def test_look(player):
    player.perform('look')
    assert player.saw('Antechamber')
    assert player.saw('columns')
    assert player.saw('Exits:')
    assert player.saw('north')
    assert player.saw('Courtyard')

def test_look_dark(player):
    player.Spatial.container.components.add(Dark())
    player.perform('look')
    assert player.saw('dark')

def test_look_visible(player, ball):
    player.perform('look')
    assert player.saw('a red ball')

def test_look_invisible(player, ghost):
    player.perform('look')
    assert player.did_not_see('ghost')

def test_look_at(player, ball):
    player.perform('look at ball')
    assert player.saw('small red')

def test_look_at_dark(player, ball):
    player.Spatial.container.components.add(Dark())
    player.perform('look at ball')
    assert player.saw('dark')

def test_look_at_ambiguous(player, box, iron_box):
    player.perform('look at box')
    assert player.saw('Which')
    player.forget()
    player.perform('1')
    assert player.saw('been through')

def test_look_in_empty(player, box):
    player.perform('look in box')
    assert player.saw('nothing')

def test_look_in_full(player, box, ball, statue, ghost):
    ball.Spatial.store_in(box)
    statue.Spatial.store_in(box)
    ghost.Spatial.store_in(box)
    player.perform('look in box')
    assert player.saw('ball')
    assert player.saw('statue')
    assert player.did_not_see('ghost')

def test_look_in_dark(player, box, ball):
    ball.Spatial.store_in(box)
    box.components.add(Dark())
    player.perform('look in box')
    assert player.saw('dark')

def test_look_in_inventory(player):
    player.perform('inv')
    assert player.saw('nothing')

def test_look_in_entity_in_inventory(player, box, ball):
    ball.Spatial.store_in(box)
    box.Spatial.store_in(player)
    player.perform('look in box')
    assert player.saw('a red ball')

def test_look_witness(player, statue):
    statue.hearing = True
    player.perform('look')
    assert statue.saw('Test Player looks around.')

def test_look_at_witness(player, statue, ghost):
    statue.hearing = True
    ghost.hearing = True
    player.perform('look at statue')
    assert statue.saw('Test Player looks at you.')
    assert ghost.saw('Test Player looks at a statue.')
