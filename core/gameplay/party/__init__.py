import os

"""Utilities for building the player party outside of the UI layer."""

from typing import Iterable, List, Sequence

from core.entities import Actor
from core.gameplay.inventory import Inventory


def _resolve_portrait_path(value):
    """Allow templates to provide either a string path or path parts."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return os.path.join(*value)
    return value


def build_party(
    templates: Sequence[dict],
    inventory: Inventory | None = None,
) -> List[Actor]:
    """Instantiate actors from template dictionaries.

    Each template must include a ``name`` key; other keys are forwarded as
    keyword arguments to ``Actor``. ``portrait_path`` values may be either a
    full path or an iterable of path segments.
    """

    party: List[Actor] = []
    for template in templates:
        data = dict(template)
        name = data.pop("name")
        loadout = data.pop("loadout", [])
        portrait_path = _resolve_portrait_path(
            data.pop("portrait_path", None)
        )
        spell_id = data.pop("spell_id", None)
        actor = Actor(
            name,
            portrait_path=portrait_path,
            spell_id=spell_id,
            **data,
        )
        for item_id in loadout:
            if inventory is not None:
                inventory.add_item(item_id)
                inventory.equip_item(actor, item_id)
        party.append(actor)
    return party


# Update this list to tweak the default roster used by the UI.
DEFAULT_PARTY_TEMPLATES: Iterable[dict] = [
    {
        "name": "Sora",
        "cd": 0.2,
        "atk": 5,
        "portrait_path": ("assets", "portraits", "sora.png"),
        "spell_id": "fire",
        "loadout": ["kingdom_key"]
    },
    {
        "name": "Donald",
        "cd": 0.3,
        "atk": 4,
        "portrait_path": ("assets", "portraits", "donald.png"),
        "spell_id": "blizzard",
        "loadout": ["mages_staff"]
    },
    {
        "name": "Goofy",
        "cd": 0.4,
        "atk": 3,
        "portrait_path": ("assets", "portraits", "goofy.png"),
        "spell_id": "thunder",
        "loadout": ["knights_shield"]
    },
]
