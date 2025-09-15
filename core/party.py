"""Utilities for building the player party outside of the UI layer."""

from typing import Iterable, List, Sequence
import os

from core.entities import Actor


def _resolve_portrait_path(value):
    """Allow templates to provide either a string path or path parts."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return os.path.join(*value)
    return value


def build_party(templates: Sequence[dict]) -> List[Actor]:
    """Instantiate actors from template dictionaries.

    Each template must include a ``name`` key; the rest are forwarded as
    keyword arguments to ``Actor``. ``portrait_path`` values may be either a
    full string path or an iterable of path segments.
    """

    party: List[Actor] = []
    for template in templates:
        data = dict(template)
        name = data.pop("name")
        portrait_path = _resolve_portrait_path(data.pop("portrait_path", None))
        actor = Actor(name, portrait_path=portrait_path, **data)
        party.append(actor)
    return party


# Update this list to tweak the default roster used by the UI.
DEFAULT_PARTY_TEMPLATES: Iterable[dict] = [
    {
        "name": "Sora",
        "cd": 0.2,
        "atk": 5,
        "portrait_path": ("assets", "portraits", "sora.png"),
    },
    {
        "name": "Donald",
        "cd": 0.3,
        "atk": 4,
        "portrait_path": ("assets", "portraits", "donald.png"),
    },
    {
        "name": "Goofy",
        "cd": 0.4,
        "atk": 3,
        "portrait_path": ("assets", "portraits", "goofy.png"),
    },
]

