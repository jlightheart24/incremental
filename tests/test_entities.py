from core.entities import Actor, Enemy

def test_actor_enemy_wiring():
    a = Actor("TEST", hp=7, atk=4, defense=1, mp_max=3, cd=0.2, mp_gain=2)
    e = Enemy(hp=9, defense=3)
    assert a.Stats.atk == 4
    assert a.health.current == 7
    assert a.mana.max == 3
    assert a.attack_profile.cooldown_s == 0.2
    assert e.stats.defense == 3
    assert e.health.current == 9