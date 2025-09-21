from typing import Callable, Iterable

from core.attack import AttackProfile, AttackState
from core.damage import calc_damage


class TickController:
    """Accumulates time and invokes a callback on fixed ticks.

    Example:
        tc = TickController(0.2)
        tc.update(0.1, on_tick)  # no tick yet
        tc.update(0.1, on_tick)  # on_tick(0.2) called once
    """

    def __init__(self, tick_length_s: float = 0.2) -> None:
        self.tick_length_s = float(tick_length_s)
        self._accum = 0.0

    def update(self, dt: float, on_tick: Callable[[float], None]) -> None:
        self._accum += float(dt)
        while self._accum >= self.tick_length_s:
            on_tick(self.tick_length_s)
            self._accum -= self.tick_length_s

    def __str__(self) -> str:
        return (
            "TickController("
            f"dt={self.tick_length_s}s, accum={self._accum:.3f})"
        )


class CombatSystem:
    """Coordinates basic attacks each tick for a set of actors vs. one enemy.

    Expected shape for an actor and enemy:
      - .stats.atk / .stats.defense
      - .health.current with .clamp()
      - .mana.current with .clamp()
      - .attack_profile.cooldown_s / .mp_gain_on_attack
      - .attack_state.tick(dt) / .ready(cooldown_s) / .reset()

    NOTE: Fill in the TODOs to wire the behavior.
    """

    def __init__(self, actors: Iterable, enemy) -> None:
        self.actors = list(actors)
        self.enemy = enemy

    def on_tick(self, dt: float) -> None:
        """Advance attack timers and perform basic attacks when ready."""
        if self.enemy.health.is_dead():
            return  # Enemy already defeated
        for actor in self.actors:
            if actor.health.is_dead():
                continue  # Skip dead actors
            actor.attack_state.tick(dt)
            if actor.attack_state.ready(actor.attack_profile.cooldown_s):
                self.basic_attack(actor, self.enemy)


    def basic_attack(self, attacker, defender) -> int:
        """Compute damage and apply it to defender; grant attacker MP.
        Returns the damage dealt.
        """
        damage = calc_damage(attacker.stats.atk, defender.stats.defense)
        if attacker.mana.full():
            damage += attacker.magic_damage
            attacker.mana.current = 0
        defender.health.current -= damage
        defender.health.clamp()
        attacker.mana.current += attacker.attack_profile.mp_gain_on_attack
        attacker.mana.clamp()
        attacker.attack_state.reset()
        return damage

    def __str__(self) -> str:
        enemy_name = type(self.enemy).__name__
        return f"CombatSystem(actors={len(self.actors)}, enemy={enemy_name})"
