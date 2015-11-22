import pytest

def test_look(player, gold):
    player.perform('look')
    assert player.saw('a gold coin (50)')

def test_get_all_implicit(player, gold):
    player.perform('get gold')
    assert player.saw('You pick up a gold coin (50).')
    player.forget()
    player.perform('look')
    assert player.did_not_see('gold coin')

def test_get_all_explicit(player, gold):
    player.perform('get all gold')
    assert player.saw('You pick up a gold coin (50).')
    player.forget()
    player.perform('look')
    assert player.did_not_see('gold coin')

def test_get_all_by_quantity(player, gold):
    player.perform('get 50 gold')
    assert player.saw('You pick up a gold coin (50).')
    player.forget()
    player.perform('look')
    assert player.did_not_see('gold coin')

def test_get_all_invalid(player):
    player.perform('get all gold')
    assert player.saw("You don't see any 'gold' nearby.")

def test_get_subset(player, gold):
    player.perform('get 10 gold')
    assert player.saw('You pick up a gold coin (10).')
    player.forget()
    player.perform('inv')
    assert player.saw('gold coin (10)')
    player.forget()
    player.perform('look')
    assert player.saw('gold coin (40)')

def test_get_zero(player, gold):
    player.perform('get 0 gold')
    assert player.saw("You're unable to do that.")

def test_get_too_many(player, gold):
    player.perform('get 999 gold')
    assert player.saw("You don't see 999 'gold' nearby.")

def test_get_combining(player, gold):
    player.perform('get 10 gold')
    player.perform('get 20 gold')
    player.forget()
    player.perform('inv')
    assert player.saw('a gold coin (30)')

def test_get_nonstackable(player, ball):
    player.perform('get 1 ball')
    assert player.saw('a red ball')

def test_get_too_many_nonstackable(player, ball):
    player.perform('get 5 ball')
    assert player.saw("You don't see 5 'ball' nearby.")

def test_drop_all_implicit(player, gold):
    player.perform('get 10 gold')
    player.forget()
    player.perform('drop gold')
    assert player.saw('You drop a gold coin (10).')

def test_drop_all_explicit(player, gold):
    player.perform('get 10 gold')
    player.forget()
    player.perform('drop all gold')
    assert player.saw('You drop a gold coin (10).')

def test_drop_subset(player, gold):
    player.perform('get 10 gold')
    player.forget()
    player.perform('drop 5 gold')
    assert player.saw('You drop a gold coin (5).')

def test_drop_too_many(player, gold):
    player.perform('get 30 gold')
    player.forget()
    player.perform('drop 999 gold')
    assert player.saw("You don't see 999 'gold' in your inventory.")

def test_drop_combining(player, gold):
    player.perform('get 10 gold')
    player.perform('drop 5 gold')
    player.perform('drop 5 gold')
    player.forget()
    player.perform('look')
    assert player.saw('a gold coin (50)')

def test_put_in_all_implicit(player, gold, box):
    player.perform('put gold in box')
    assert player.saw('a gold coin (50) in a cardboard box')
    player.forget()
    player.perform('look')
    assert player.did_not_see('gold coin')

def test_put_in_all_explicit(player, gold, box):
    player.perform('put all gold in box')
    assert player.saw('a gold coin (50) in a cardboard box')
    player.forget()
    player.perform('look')
    assert player.did_not_see('gold coin')

def test_put_in_subset(player, gold, box):
    player.perform('put 20 gold in box')
    assert player.saw('a gold coin (20) in a cardboard box')
    player.forget()
    player.perform('look')
    assert player.saw('gold coin (30)')
    player.forget()
    player.perform('look in box')
    assert player.saw('gold coin (20)')

def test_put_in_too_many(player, gold, box):
    player.perform('put 999 gold in box')
    assert player.saw("You don't see 999 'gold' nearby.")

def test_put_in_combining(player, gold, box):
    player.perform('put 5 gold in box')
    player.perform('put 5 gold in box')
    player.forget()
    player.perform('look in box')
    assert player.saw('a gold coin (10)')

def test_put_in_ambiguous(player, gold, box):
    player.perform('get 5 gold')
    player.perform('put 5 gold in box')
    assert player.saw('Which')
    assert player.saw('a gold coin (5) (in inventory)')
    player.forget()
    player.perform('1')  # XXX: Could be from inv, could be from room
    assert player.saw('a gold coin (5) in a cardboard box')

def test_put_in_semiambiguous(player, gold, box):
    player.perform('get 45 gold')
    # Would be ambiguous if not for minimum quantity
    player.perform('put 45 gold in box')
    assert player.saw('a gold coin (45) in a cardboard box')

def test_get_from_all_implicit(player, gold, box):
    gold.Spatial.store_in(box)
    player.perform('get gold from box')
    assert player.saw('a gold coin (50) from a cardboard box')
    player.forget()
    player.perform('look in box')
    assert player.did_not_see('gold coin')

def test_get_from_all_explicit(player, gold, box):
    gold.Spatial.store_in(box)
    player.perform('get all gold from box')
    assert player.saw('a gold coin (50) from a cardboard box')
    player.forget()
    player.perform('look in box')
    assert player.did_not_see('gold coin')

def test_get_from_subset(player, gold, box):
    gold.Spatial.store_in(box)
    player.perform('get 20 gold from box')
    assert player.saw('a gold coin (20) from a cardboard box')
    player.forget()
    player.perform('look in box')
    assert player.saw('gold coin (30)')
    player.forget()
    player.perform('inv')
    assert player.saw('gold coin (20)')

def test_get_from_too_many(player, gold, box):
    gold.Spatial.store_in(box)
    player.perform('get 999 gold from box')
    assert player.saw("You don't see 999 'gold' in a cardboard box.")

def test_get_from_combining(player, gold, box):
    gold.Spatial.store_in(box)
    player.perform('get 5 gold from box')
    player.perform('get 5 gold from box')
    player.forget()
    player.perform('inv')
    assert player.saw('a gold coin (10)')
