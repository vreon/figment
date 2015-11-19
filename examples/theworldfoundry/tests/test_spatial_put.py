def test_put_in(player, ball, box):
    player.perform('put ball in box')
    assert player.saw('put a red ball in a cardboard box')

def test_put_in_invalid(player, ball):
    player.perform('put ball in hoop')
    assert player.saw("There's no hoop")

def test_put_in_noncontainer(player, ball, statue):
    player.perform('put ball in statue')
    assert player.saw("statue can't hold things")

def test_put_uncarriable(player, statue, box):
    player.perform('put statue in box')
    assert player.saw("can't be carried")

def test_put_from_inventory(player, ball, box):
    ball.Spatial.store_in(player)
    player.perform('put ball in box')
    assert player.saw('put a red ball in a cardboard box')

def test_drop(player, ball, box):
    ball.Spatial.store_in(player)
    player.perform('drop ball')
    assert player.saw('You drop a red ball')
