import unittest


# Test doubles and imports kept minimal to focus on CombatSystem behavior.
from core.combat import TickController, CombatSystem
from core.stats import Stats, Health, Mana
from core.attack import AttackProfile, AttackState


class TestAttackState(AttackState):
    """Concrete AttackState for tests with a working ready() method."""

    def ready(self, cooldown_s):
        return self.time_since_attack_s >= float(cooldown_s)


class Actor:
    def __init__(
        self,
        *,
        hp=10,
        atk=5,
        defense=1,
        speed=1,
        mp_max=10,
        cd=0.2,
        mp_gain=1,
    ):
        self.stats = Stats(
            max_hp=hp,
            atk=atk,
            defense=defense,
            speed=speed,
            mp_max=mp_max,
        )
        self.health = Health(current=hp, max=hp)
        self.mana = Mana(current=0, max=mp_max)
        self.attack_profile = AttackProfile(
            cooldown_s=cd,
            mp_gain_on_attack=mp_gain,
        )
        self.attack_state = TestAttackState()


class Enemy:
    def __init__(self, *, hp=20, atk=3, defense=2, speed=1, cd=0.8):
        self.stats = Stats(max_hp=hp, atk=atk, defense=defense, speed=speed)
        self.health = Health(current=hp, max=hp)
        self.attack_profile = AttackProfile(cooldown_s=cd, mp_gain_on_attack=0)
        self.attack_state = TestAttackState()


class SpyCombat(CombatSystem):
    def __init__(self, actors, enemy):
        super().__init__(
            actors,
            enemy,
            select_enemy_target=lambda _: None,
        )
        self.attacks = []

    def basic_attack(self, attacker, defender) -> int:
        # Record the call and return a sentinel damage value
        self.attacks.append((attacker, defender))
        return 0


class TickControllerTests(unittest.TestCase):
    def test_calls_on_fixed_threshold(self):
        tc = TickController(0.2)
        calls = []

        def cb(dt):
            calls.append(dt)

        tc.update(0.05, cb)
        self.assertEqual(calls, [])

        tc.update(0.10, cb)
        self.assertEqual(calls, [])

        tc.update(0.05, cb)
        self.assertEqual(calls, [0.2])

        tc.update(0.40, cb)
        # 0.40 accumulates into two more ticks of 0.2
        self.assertEqual(calls, [0.2, 0.2, 0.2])


class CombatOnTickTests(unittest.TestCase):
    def test_actor_attacks_once_when_cooldown_reached(self):
        a = Actor(cd=0.2)
        e = Enemy()
        cs = SpyCombat([a], e)

        cs.on_tick(0.10)  # not ready
        self.assertEqual(len(cs.attacks), 0)

        cs.on_tick(0.10)  # reaches 0.2
        self.assertEqual(len(cs.attacks), 1)
        self.assertIs(cs.attacks[0][0], a)
        self.assertIs(cs.attacks[0][1], e)

    def test_skips_dead_actor_and_stops_if_enemy_dead(self):
        a1 = Actor(cd=0.1)
        a2 = Actor(cd=0.1)
        e = Enemy()
        cs = SpyCombat([a1, a2], e)

        # Kill a1, ensure it does not act
        a1.health.current = 0
        a1.health.clamp()

        cs.on_tick(0.1)
        self.assertEqual(len(cs.attacks), 1)
        self.assertIs(cs.attacks[0][0], a2)

        # Now kill the enemy; further ticks should early-return
        e.health.current = 0
        e.health.clamp()

        cs.on_tick(1.0)
        self.assertEqual(len(cs.attacks), 1)  # unchanged


class CombatBasicAttackTests(unittest.TestCase):
    def test_basic_attack_applies_damage_grants_mp_and_resets(self):
        # Arrange
        a = Actor(hp=10, atk=5, defense=0, mp_max=3, cd=0.2, mp_gain=2)
        e = Enemy(hp=9, defense=3)

        class CS(CombatSystem):
            pass

        cs = CS([a], e)

        # Make sure attack state has progressed, so we can see it reset to 0
        a.attack_state.tick(0.5)
        self.assertGreater(a.attack_state.time_since_attack_s, 0.0)

        # Act
        # NOTE: Requires damage spec max(1, atk - defense).
        dmg = cs.basic_attack(a, e)

        # Assert damage math and HP change
        expected = max(1, a.stats.atk - e.stats.defense)
        self.assertEqual(dmg, expected)
        self.assertEqual(e.health.current, 9 - expected)

        # Assert MP granted and clamped to mp_max
        expected_mp = min(
            a.mana.max,
            0 + a.attack_profile.mp_gain_on_attack,
        )
        self.assertEqual(a.mana.current, expected_mp)

        # Assert attack state reset
        self.assertEqual(a.attack_state.time_since_attack_s, 0.0)


if __name__ == "__main__":
    unittest.main()
