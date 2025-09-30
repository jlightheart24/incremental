import random
from typing import Dict, Iterable, List

from core.entities import Enemy


ENEMY_DEFINITIONS: Dict[str, dict] = {
    "shadow": {
        "name": "Shadow",
        "hp": 22,
        "atk": 2,
        "defense": 1,
        "cd": 2.5,
        "portrait_path": "assets/portraits/enemies/shadow.png",
        "xp_reward": 12,
        "munny_reward": 6,
        "drops": [
            {
                "material_id": "bright_shard",
                "chance": 0.5,
                "amount": 1,
            },
            {
                "material_id": "dark_shard",
                "chance": 0.4,
                "amount": 1,
            },
        ],
    },
    "soldier": {
        "name": "Soldier",
        "hp": 24,
        "atk": 2,
        "defense": 1,
        "cd": 2.0,
        "portrait_path": "assets/portraits/enemies/soldier.png",
        "xp_reward": 24,
        "munny_reward": 12,
        "drops": [
            {
                "item_id": "champion_belt",
                "chance": 0.25,
            },
            {
                "material_id": "mythril_fragment",
                "chance": 0.5,
                "amount": 1,
            },
        ],
    },
}


class EncounterPool:
    """Manage enemy templates and spawn new instances on demand."""

    def __init__(
        self,
        pools: Dict[str, Iterable[dict]],
        *,
        default_pool: str,
        enemy_definitions: Dict[str, dict] | None = None,
    ):
        if default_pool not in pools:
            raise KeyError(f"Unknown enemy pool '{default_pool}'")
        # Copy each template so edits here never touch caller data.
        self._pools: Dict[str, List[dict]] = {}
        for name, entries in pools.items():
            self._pools[name] = [dict(entry) for entry in entries]
        self._current_pool = default_pool
        self._rng = random.Random()
        self._enemy_definitions = {
            key: dict(value)
            for key, value in (enemy_definitions or ENEMY_DEFINITIONS).items()
        }

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
        if "enemy_id" in template:
            enemy_id = template.pop("enemy_id")
            try:
                base = dict(self._enemy_definitions[enemy_id])
            except KeyError as exc:
                raise KeyError(
                    f"Encounter references unknown enemy id '{enemy_id}'"
                ) from exc
            merged = {**base, **template}
        else:
            merged = template
        xp_reward = merged.pop("xp_reward", 0)
        munny_reward = merged.pop(
            "munny_reward",
            merged.pop("gold_reward", 0),
        )
        drops = merged.pop("drops", None)
        level = int(merged.pop("level", merged.pop("enemy_level", 1)) or 1)
        enemy = Enemy(
            **merged,
            xp_reward=xp_reward,
            munny_reward=munny_reward,
            drops=drops,
            level=level,
        )
        return enemy


DEFAULT_ENCOUNTER_POOLS = {
    # Beachfront Heartless patrols for the Destiny Islands starting scenario.
    "destiny_islands_beach": [
        {"enemy_id": "shadow", "level": 1},
        {"enemy_id": "soldier", "level": 2},
    ],
    "destiny_islands_cove": [
        {"enemy_id": "shadow", "level": 2, "xp_reward": 16, "munny_reward": 10},
        {
            "enemy_id": "soldier",
            "level": 3,
            "xp_reward": 32,
            "munny_reward": 18,
            "drops": [
                {
                    "item_id": "champion_belt",
                    "chance": 0.4,
                },
                {
                    "material_id": "mythril_fragment",
                    "chance": 0.65,
                    "amount": 1,
                },
            ],
        },
    ],
}
