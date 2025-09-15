import random
from typing import Dict, Iterable, List

from core.entities import Enemy


class EncounterPool:
    """Manage collections of enemy templates and spawn new instances on demand."""

    def __init__(self, pools: Dict[str, Iterable[dict]], *, default_pool: str):
        if default_pool not in pools:
            raise KeyError(f"Unknown enemy pool '{default_pool}'")
        # Copy each template so edits here never mutate the caller's data structures.
        self._pools: Dict[str, List[dict]] = {
            name: [dict(entry) for entry in entries] for name, entries in pools.items()
        }
        self._current_pool = default_pool
        self._rng = random.Random()

    @property
    def current_pool(self) -> str:
        return self._current_pool

    def set_pool(self, pool_name: str) -> None:
        if pool_name not in self._pools:
            raise KeyError(f"Unknown enemy pool '{pool_name}'")
        self._current_pool = pool_name

    def add_enemy(self, pool_name: str, template: dict) -> None:
        # Append a new template to a pool; handy when tweaking encounters at runtime.
        self._pools.setdefault(pool_name, []).append(dict(template))

    def next_enemy(self) -> Enemy:
        candidates = self._pools.get(self._current_pool)
        if not candidates:
            raise ValueError(f"Enemy pool '{self._current_pool}' is empty")
        template = dict(self._rng.choice(candidates))
        xp_reward = template.pop("xp_reward", 0)
        enemy = Enemy(**template)
        enemy.xp_reward = xp_reward
        return enemy


DEFAULT_ENCOUNTER_POOLS = {
    # Edit these entries (or add more pools) to control what the UI can spawn.
    "shadowlands": [
        {
            "hp": 25,
            "atk": 1,
            "defense": 1,
            "portrait_path": "assets/portraits/enemies/shadow.png",
            "xp_reward": 10,
        },
        {
            "hp": 100,
            "atk": 5,
            "defense": 2,
            "portrait_path": "assets/portraits/enemies/soldier.png",
            "xp_reward": 25,
        }
    ]
}
