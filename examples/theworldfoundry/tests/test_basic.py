def test_invalid(player):
    player.perform("lerp")
    assert player.saw("Unknown command")
