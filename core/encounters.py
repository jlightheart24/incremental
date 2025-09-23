import random
from typing import Dict, Iterable, List

from core.entities import Enemy


class EncounterPool:
    """Manage enemy templates and spawn new instances on demand."""

    def __init__(self, pools: Dict[str, Iterable[dict]], *, default_pool: str):
        if default_pool not in pools:
            raise KeyError(f"Unknown enemy pool '{default_pool}'")
        # Copy each template so edits here never touch caller data.
        self._pools: Dict[str, List[dict]] = {}
        for name, entries in pools.items():
            self._pools[name] = [dict(entry) for entry in entries]
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
        # Append a new template to a pool when tweaking encounters at runtime.
        self._pools.setdefault(pool_name, []).append(dict(template))

    def next_enemy(self) -> Enemy:
        candidates = self._pools.get(self._current_pool)
        if not candidates:
            raise ValueError(f"Enemy pool '{self._current_pool}' is empty")
        template = dict(self._rng.choice(candidates))
        xp_reward = template.pop("xp_reward", 0)
        munny_reward = template.pop(
            "munny_reward",
            template.pop("gold_reward", 0),
        )
        drops = template.pop("drops", None)
        enemy = Enemy(
            **template,
            xp_reward=xp_reward,
            munny_reward=munny_reward,
            drops=drops,
        )
        return enemy


DEFAULT_ENCOUNTER_POOLS = {
    # Edit these entries (or add more pools) to control what the UI can spawn.
    "shadowlands": [
        {
            "hp": 25,
            "atk": 1,
            "defense": 1,
            "cd": 3,
            "portrait_path": "assets/portraits/enemies/shadow.png",
            "xp_reward": 10,
            "munny_reward": 5,
            "drops": [
                {
                    "item_id": "elven_bandana",
                    "chance": 0.3,
                },
                {
                    "material_id": "dark_shard",
                    "chance": 0.8,
                    "amount": 2,
                },
                {
                    "material_id": "bright_shard",
                    "chance": 0.5,
                    "amount": 1,
                },
            ],
        },
        {
            "hp": 100,
            "atk": 5,
            "defense": 2,
            "cd":2,
            "portrait_path": "assets/portraits/enemies/soldier.png",
            "xp_reward": 25,
            "munny_reward": 10,
            "drops": [
                {
                    "item_id": "champion_belt",
                    "chance": 0.3,
                },
                {
                    "material_id": "mythril_fragment",
                    "chance": 0.6,
                    "amount": 1,
                },
                {
                    "material_id": "dark_shard",
                    "chance": 0.4,
                    "amount": 1,
                },
            ],
        }
    ]
}
