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
