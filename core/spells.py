"""Central spell definitions and helpers."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Spell:
    spell_id: str
    name: str
    mp_max: int
    damage: int


SPELL_BOOK: Dict[str, Spell] = {
    "fire": Spell("fire", "Fire", mp_max=10, damage=18),
    "blizzard": Spell("blizzard", "Blizzard", mp_max=14, damage=24),
    "thunder": Spell("thunder", "Thunder", mp_max=12, damage=20),
}


def get_spell(spell_id: str) -> Spell:
    try:
        return SPELL_BOOK[spell_id]
    except KeyError as exc:
        raise KeyError(f"Unknown spell '{spell_id}'") from exc


def spell_ids() -> List[str]:
    return list(SPELL_BOOK.keys())


def default_spell() -> Spell:
    """Return the first spell in the configured book."""
    return next(iter(SPELL_BOOK.values()))
