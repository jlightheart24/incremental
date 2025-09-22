from __future__ import annotations

from core.attack import AttackProfile, AttackState
from core.stats import Health, Stats


class Character:
    """Common combat state shared by actors and enemies."""

    def __init__(
        self,
        name: str,
        *,
        hp: int = 10,
        atk: int = 5,
        defense: int = 1,
        speed: int = 1,
        mp_max: int = 10,
        cd: float = 0.2,
        mp_gain: int = 0,
        portrait_path: str | None = None,
    ) -> None:
        self.name = name
        self.portrait_path = portrait_path
        self.stats = Stats(
            max_hp=hp,
            atk=atk,
            defense=defense,
            speed=speed,
            mp_max=mp_max,
        )
        self.health = Health(current=hp, max=hp)
        self.attack_profile = AttackProfile(
            cooldown_s=cd,
            mp_gain_on_attack=mp_gain,
        )
        self.attack_state = AttackState()

    def __str__(self) -> str:
        return f"{self.name}(HP={self.health.current})"
