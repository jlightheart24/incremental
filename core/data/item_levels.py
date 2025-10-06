"""Level-up requirements for equippable items."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class ItemLevelRequirement:
    """Materials and duplicate costs for reaching a specific item level."""

    level: int
    item_cost: int
    materials: Dict[str, int]


# Requirements are defined for the *target* level (e.g. entry with level=2
# represents the materials required to go from level 1 -> level 2).
ITEM_LEVEL_TABLE: Dict[str, Tuple[ItemLevelRequirement, ...]] = {
    "kingdom_key": (
        ItemLevelRequirement(level=2, item_cost=1, materials={"bright_shard": 1}),
        ItemLevelRequirement(
            level=3,
            item_cost=1,
            materials={"bright_shard": 2, "dark_shard": 1},
        ),
        ItemLevelRequirement(
            level=4,
            item_cost=2,
            materials={"bright_shard": 2, "dark_shard": 2},
        ),
        ItemLevelRequirement(
            level=5,
            item_cost=2,
            materials={"bright_shard": 3, "dark_shard": 2, "mythril_fragment": 1},
        ),
    ),
    "mages_staff": (
        ItemLevelRequirement(level=2, item_cost=1, materials={"bright_shard": 1}),
        ItemLevelRequirement(
            level=3,
            item_cost=1,
            materials={"bright_shard": 1, "dark_shard": 1, "mythril_fragment": 1},
        ),
        ItemLevelRequirement(
            level=4,
            item_cost=2,
            materials={"bright_shard": 2, "dark_shard": 2, "mythril_fragment": 1},
        ),
        ItemLevelRequirement(
            level=5,
            item_cost=2,
            materials={"bright_shard": 2, "dark_shard": 2, "mythril_fragment": 2},
        ),
    ),
    "knights_shield": (
        ItemLevelRequirement(level=2, item_cost=1, materials={"dark_shard": 1}),
        ItemLevelRequirement(
            level=3,
            item_cost=1,
            materials={"dark_shard": 2, "mythril_fragment": 1},
        ),
        ItemLevelRequirement(
            level=4,
            item_cost=2,
            materials={"dark_shard": 3, "mythril_fragment": 1},
        ),
        ItemLevelRequirement(
            level=5,
            item_cost=2,
            materials={"dark_shard": 3, "mythril_fragment": 2},
        ),
    ),
    "champion_belt": (
        ItemLevelRequirement(level=2, item_cost=1, materials={"mythril_fragment": 1}),
        ItemLevelRequirement(
            level=3,
            item_cost=1,
            materials={"dark_shard": 1, "mythril_fragment": 2},
        ),
        ItemLevelRequirement(
            level=4,
            item_cost=2,
            materials={"dark_shard": 1, "mythril_fragment": 3},
        ),
        ItemLevelRequirement(
            level=5,
            item_cost=2,
            materials={"dark_shard": 2, "mythril_fragment": 3},
        ),
    ),
    "heros_crest": (
        ItemLevelRequirement(level=2, item_cost=1, materials={"bright_shard": 1}),
        ItemLevelRequirement(
            level=3,
            item_cost=1,
            materials={"bright_shard": 2, "mythril_fragment": 1},
        ),
        ItemLevelRequirement(
            level=4,
            item_cost=2,
            materials={"bright_shard": 2, "mythril_fragment": 2},
        ),
        ItemLevelRequirement(
            level=5,
            item_cost=2,
            materials={"bright_shard": 3, "mythril_fragment": 2},
        ),
    ),
    "elven_bandana": (
        ItemLevelRequirement(level=2, item_cost=1, materials={"bright_shard": 1}),
        ItemLevelRequirement(
            level=3,
            item_cost=1,
            materials={"bright_shard": 1, "dark_shard": 1},
        ),
        ItemLevelRequirement(
            level=4,
            item_cost=2,
            materials={"bright_shard": 2, "dark_shard": 1},
        ),
        ItemLevelRequirement(
            level=5,
            item_cost=2,
            materials={"bright_shard": 2, "dark_shard": 2},
        ),
    ),
}


def iter_level_requirements(item_id: str) -> Iterable[ItemLevelRequirement]:
    """Yield the configured level requirements for an item."""

    return ITEM_LEVEL_TABLE.get(item_id, ())


def requirement_for_level(
    item_id: str,
    target_level: int,
) -> ItemLevelRequirement | None:
    requirements = ITEM_LEVEL_TABLE.get(item_id)
    if not requirements:
        return None
    for requirement in requirements:
        if requirement.level == target_level:
            return requirement
    return None


def max_level(item_id: str) -> int:
    requirements = ITEM_LEVEL_TABLE.get(item_id)
    if not requirements:
        return 1
    return requirements[-1].level


__all__ = [
    "ItemLevelRequirement",
    "ITEM_LEVEL_TABLE",
    "iter_level_requirements",
    "requirement_for_level",
    "max_level",
]
