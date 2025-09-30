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
        level: int = 1,
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
        self.level = max(1, int(level))
        self._base_stats = {
            "hp": int(hp),
            "atk": int(atk),
            "defense": int(defense),
            "speed": int(speed),
        }
        self.xp_reward = xp_reward
        self.munny_reward = munny_reward
        self.drops = list(drops) if drops else []
        self._apply_level_scaling()

    def __str__(self) -> str:
        return f"{self.name}(Lv{self.level} HP={self.health.current})"

    def _apply_level_scaling(self) -> None:
        if self.level <= 1:
            return

        multiplier = float(self.level)

        def scale(value: int) -> int:
            return max(1, int(round(value * multiplier)))

        self.stats.max_hp = scale(self._base_stats["hp"])
        self.health.max = self.stats.max_hp
        self.health.current = self.health.max
        self.stats.atk = scale(self._base_stats["atk"])
        self.stats.defense = scale(self._base_stats["defense"])
        self.stats.speed = scale(self._base_stats["speed"])
