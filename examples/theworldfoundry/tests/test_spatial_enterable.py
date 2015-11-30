def test_enter(player, limo):
    player.perform('enter limo')
    assert player.saw('You enter a fancy limo')
    assert player.saw('electric')

def test_enter_and_exit(player, limo):
    player.perform('enter limo')
    player.forget()
    player.perform('go out')
    assert player.saw('Antechamber')
