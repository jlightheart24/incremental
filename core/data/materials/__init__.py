"""Definitions for synthesis materials."""

import copy
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Material:
    name: str
    description: str = ""


MATERIAL_DB: Dict[str, Material] = {
    "dark_shard": Material(
        name="Dark Shard",
        description="A shard pulsing with shadowy energy.",
    ),
    "bright_shard": Material(
        name="Bright Shard",
        description="A shard that glimmers with condensed light.",
    ),
    "mythril_fragment": Material(
        name="Mythril Fragment",
        description="A sliver of mythril prized by craftsmen.",
    ),
}


def get_material(material_id: str) -> Material:
    try:
        template = MATERIAL_DB[material_id]
    except KeyError as exc:
        raise KeyError(f"Unknown material '{material_id}'") from exc
    return copy.deepcopy(template)


def material_name(material_id: str) -> str:
    material = MATERIAL_DB.get(material_id)
    if material is None:
        return material_id.replace("_", " ").title()
    return material.name


__all__ = ["Material", "MATERIAL_DB", "get_material", "material_name"]
