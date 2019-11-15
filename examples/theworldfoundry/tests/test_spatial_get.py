def test_get(player, ball):
    player.perform("get ball")
    assert player.saw("pick up a red ball")
    player.forget()
    player.perform("inv")
    assert player.saw("a red ball")


def test_get_self(player):
    player.perform("get self")
    assert player.saw("can't")


def test_get_uncarriable(player, statue):
    player.perform("get statue")
    assert player.saw("can't be carried")


def test_get_from(player, ball, box):
    ball.Spatial.store_in(box)
    player.perform("get ball from box")
    assert player.saw("a red ball")
    player.forget()
    player.perform("inv")
    assert player.saw("a red ball")


def test_get_from_ambiguous(player, box, iron_box, ball, green_ball):
    ball.Spatial.store_in(box)
    green_ball.Spatial.store_in(box)
    player.perform("get ball from box")
    assert player.saw("Which 'box'")
    player.forget()
    player.perform("1")
    assert player.saw("Which 'ball'")
    player.forget()
    player.perform("1")
    assert player.saw("red ball")


def test_get_from_entity_in_inventory(player, box, ball, green_ball):
    ball.Spatial.store_in(box)
    box.Spatial.store_in(player)
    player.perform("get ball from box")
    assert player.saw("a red ball")


def test_get_from_too_deep(player, box, iron_box, ball):
    ball.Spatial.store_in(box)
    box.Spatial.store_in(iron_box)
    player.perform("get ball from box")
    assert player.saw("You don't see any 'ball' in an iron box")
    player.perform("get ball from cardboard box")
    assert player.saw("You don't see any 'cardboard box' nearby")
