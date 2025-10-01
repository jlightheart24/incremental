from __future__ import annotations

from typing import Callable, Iterable, Optional, TYPE_CHECKING

from core.gameplay.damage import calc_damage


if TYPE_CHECKING:
    from core.entities.character import Character


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
    """Coordinates combat ticks between party actors and a single enemy."""

    def __init__(
        self,
        actors: Iterable[Character],
        enemy: Character,
        *,
        select_actor_target: Optional[Callable[[Character], Optional[Character]]] = None,
        select_enemy_target: Optional[Callable[[Character], Optional[Character]]] = None,
    ) -> None:
        self.actors = list(actors)
        self.enemy: Character = enemy
        self._select_actor_target = (
            select_actor_target if select_actor_target is not None else self._default_actor_target
        )
        self._select_enemy_target = (
            select_enemy_target if select_enemy_target is not None else self._default_enemy_target
        )

    def _default_actor_target(self, actor: Character) -> Optional[Character]:
        return self.enemy

    def _default_enemy_target(self, enemy: Character) -> Optional[Character]:
        for actor in self.actors:
            if actor.health.is_dead():
                continue
            return actor
        return None

    def on_tick(self, dt: float) -> None:
        """Advance attack timers and perform basic attacks when ready."""
        for actor in self.actors:
            if actor.health.is_dead():
                continue
            actor.attack_state.tick(dt)
            if not actor.attack_state.ready(actor.attack_profile.cooldown_s):
                continue
            target = self._select_actor_target(actor)
            if target is None or target.health.is_dead():
                continue
            self.basic_attack(actor, target)

        if self.enemy.health.is_dead():
            return

        self.enemy.attack_state.tick(dt)
        if not self.enemy.attack_state.ready(self.enemy.attack_profile.cooldown_s):
            return

        target = self._select_enemy_target(self.enemy)
        if target is None or target.health.is_dead():
            return
        self.basic_attack(self.enemy, target)

    def basic_attack(self, attacker: Character, defender: Character) -> int:
        """Compute damage and apply it to defender; grant attacker MP.
        Returns the damage dealt.
        """
        damage = calc_damage(attacker.stats.atk, defender.stats.defense)
        mana = getattr(attacker, "mana", None)
        if mana is not None and mana.full():
            damage += getattr(attacker, "magic_damage", 0)
            mana.current = 0
        defender.health.current -= damage
        defender.health.clamp()
        if mana is not None:
            mana.current += attacker.attack_profile.mp_gain_on_attack
            mana.clamp()
        attacker.attack_state.reset()
        return damage

    def __str__(self) -> str:
        enemy_name = type(self.enemy).__name__
        return f"CombatSystem(actors={len(self.actors)}, enemy={enemy_name})"
