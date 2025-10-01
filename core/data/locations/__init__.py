"""Static location metadata for world/map selection."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class LocationDef:
    location_id: str
    world_id: str
    title: str
    subtitle: str
    encounter_pool: str
    background_image: str | None = None


_DESTINY_ISLANDS_BG_DIR = os.path.join("assets", "backgrounds")
_TRAVERSE_TOWN_BG_DIR = os.path.join("assets", "backgrounds")

_LOCATIONS: Dict[str, LocationDef] = {
    "destiny_islands_beach": LocationDef(
        location_id="destiny_islands_beach",
        world_id="destiny_islands",
        title="Destiny Islands",
        subtitle="Beach",
        encounter_pool="destiny_islands_beach",
        background_image=os.path.join(_DESTINY_ISLANDS_BG_DIR, "destiny_islands.png"),
    ),
    "destiny_islands_cove": LocationDef(
        location_id="destiny_islands_cove",
        world_id="destiny_islands",
        title="Destiny Islands",
        subtitle="Cove",
        encounter_pool="destiny_islands_cove",
        background_image=os.path.join(_DESTINY_ISLANDS_BG_DIR, "destiny_islands.png"),
    ),
    "traverse_town_first_district": LocationDef(
        location_id="traverse_town_first_district",
        world_id="traverse_town",
        title="Traverse Town",
        subtitle="First District",
        encounter_pool="traverse_town_first_district",
        background_image=os.path.join(_TRAVERSE_TOWN_BG_DIR, "traverse_town.png"),
    ),
    "traverse_town_second_district": LocationDef(
        location_id="traverse_town_second_district",
        world_id="traverse_town",
        title="Traverse Town",
        subtitle="Second District",
        encounter_pool="traverse_town_second_district",
        background_image=os.path.join(_TRAVERSE_TOWN_BG_DIR, "traverse_town.png"),
    ),
}

DEFAULT_LOCATION_ID = "destiny_islands_beach"


def get_location(location_id: str) -> LocationDef:
    try:
        return _LOCATIONS[location_id]
    except KeyError as exc:
        raise KeyError(f"Unknown location '{location_id}'") from exc


def iter_locations() -> Iterable[LocationDef]:
    return _LOCATIONS.values()


__all__ = [
    "LocationDef",
    "DEFAULT_LOCATION_ID",
    "get_location",
    "iter_locations",
]
