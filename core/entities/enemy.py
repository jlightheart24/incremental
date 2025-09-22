from __future__ import annotations

from core.entities.character import Character


class Enemy(Character):
    def __init__(
        self,
        *,
        name: str = "Enemy",
        hp: int = 20,
        atk: int = 3,
        defense: int = 2,
        speed: int = 1,
        mp_max: int = 0,
        cd: float = 0.8,
        mp_gain: int = 0,
        portrait_path: str | None = None,
        xp_reward: int = 50,
        munny_reward: int = 0,
        drops: list | None = None,
    ) -> None:
        super().__init__(
            name,
            hp=hp,
            atk=atk,
            defense=defense,
            speed=speed,
            mp_max=mp_max,
            cd=cd,
            mp_gain=mp_gain,
            portrait_path=portrait_path,
        )
        self.xp_reward = xp_reward
        self.munny_reward = munny_reward
        self.drops = list(drops) if drops else []

    def __str__(self) -> str:
        return f"{self.name}(HP={self.health.current})"
