from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from core.data.items import get_item
from core.data.locations import DEFAULT_LOCATION_ID, get_location
from core.data.spells import get_spell
from core.entities import Actor
from core.gameplay.inventory import Inventory
from core.gameplay.party import DEFAULT_PARTY_TEMPLATES, build_party

SAVE_DIR_ENV = "INCREMENTAL_SAVE_DIR"
SAVE_VERSION = 1
SAVE_FILE_SUFFIX = ".json"
DEFAULT_MAX_SLOTS = 3


@dataclass
class SaveSlotInfo:
    slot_id: str
    title: str
    exists: bool
    updated_at: datetime | None = None
    location_id: str | None = None
    party: List[str] = field(default_factory=list)
    munny: int = 0

    def location_display(self) -> str:
        if not self.location_id:
            return "Unknown"
        try:
            location = get_location(self.location_id)
        except KeyError:
            return self.location_id
        return location.title


@dataclass
class GameState:
    slot_id: str
    location_id: str
    inventory: Inventory
    actors: List[Actor]
    created_at: datetime | None = None
    updated_at: datetime | None = None
    summary: Dict[str, Any] = field(default_factory=dict)


def _resolve_save_dir(base_path: str | os.PathLike[str] | None = None) -> Path:
    if base_path is not None:
        return Path(base_path)
    env_path = os.environ.get(SAVE_DIR_ENV)
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parents[2] / "saves"


def _slot_path(slot_id: str, *, base_path: str | os.PathLike[str] | None = None) -> Path:
    directory = _resolve_save_dir(base_path)
    return directory / f"{slot_id}{SAVE_FILE_SUFFIX}"


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _serialize_inventory(inventory: Inventory) -> Dict[str, Any]:
    return {
        "capacity": dict(inventory.capacity),
        "items_by_slot": {
            slot: list(items)
            for slot, items in inventory.items_by_slot.items()
        },
        "item_list": list(inventory.item_list),
        "munny": int(inventory.munny),
        "materials": {
            material_id: int(amount)
            for material_id, amount in inventory.materials.items()
        },
    }


def _serialize_actor(actor: Actor) -> Dict[str, Any]:
    equipment = {}
    if hasattr(actor, "equipment") and isinstance(actor.equipment, dict):
        for slot, entry in actor.equipment.items():
            if isinstance(entry, tuple) and entry:
                equipment[slot] = entry[0]
    return {
        "name": actor.name,
        "portrait_path": actor.portrait_path,
        "stats": {
            "max_hp": actor.stats.max_hp,
            "atk": actor.stats.atk,
            "defense": actor.stats.defense,
            "speed": actor.stats.speed,
            "mp_max": actor.stats.mp_max,
        },
        "health": {
            "current": actor.health.current,
            "max": actor.health.max,
        },
        "mana": {
            "current": getattr(actor, "mana", None).current if hasattr(actor, "mana") else 0,
            "max": getattr(actor, "mana", None).max if hasattr(actor, "mana") else 0,
        },
        "magic_damage": getattr(actor, "magic_damage", 0),
        "level": getattr(actor, "level", 1),
        "xp": getattr(actor, "xp", 0),
        "xp_to_level": getattr(actor, "xp_to_level", 0),
        "spell_id": getattr(actor, "spell_id", None),
        "attack_profile": {
            "cooldown_s": actor.attack_profile.cooldown_s,
            "mp_gain": actor.attack_profile.mp_gain_on_attack,
        },
        "equipment": equipment,
    }


def _build_inventory(payload: Dict[str, Any]) -> Inventory:
    capacity = payload.get("capacity", {})
    inventory = Inventory(
        keyblade_slots=int(capacity.get("keyblade", 0)),
        armor_slots=int(capacity.get("armor", 0)),
        accessory_slots=int(capacity.get("accessory", 0)),
    )
    inventory.items_by_slot = defaultdict(
        list,
        {
            slot: list(items)
            for slot, items in payload.get("items_by_slot", {}).items()
        },
    )
    inventory.item_list = list(payload.get("item_list", []))
    inventory.munny = int(payload.get("munny", 0))
    inventory.materials = defaultdict(
        int,
        {
            material_id: int(amount)
            for material_id, amount in payload.get("materials", {}).items()
        },
    )
    return inventory


def _build_actor(payload: Dict[str, Any]) -> Actor:
    stats = payload.get("stats", {})
    attack_profile = payload.get("attack_profile", {})
    mana_payload = payload.get("mana", {})
    health_payload = payload.get("health", {})
    actor = Actor(
        payload.get("name", "Actor"),
        hp=int(stats.get("max_hp", 10)),
        atk=int(stats.get("atk", 5)),
        defense=int(stats.get("defense", 1)),
        speed=int(stats.get("speed", 1)),
        mp_max=int(stats.get("mp_max", mana_payload.get("max", 10))),
        cd=float(attack_profile.get("cooldown_s", 0.2)),
        mp_gain=int(attack_profile.get("mp_gain", 1)),
        portrait_path=payload.get("portrait_path"),
        level=int(payload.get("level", 1)),
        xp=int(payload.get("xp", 0)),
        spell_id=None,
    )
    actor.health.max = int(health_payload.get("max", actor.health.max))
    actor.health.current = int(health_payload.get("current", actor.health.current))
    if hasattr(actor, "mana"):
        actor.mana.max = int(mana_payload.get("max", actor.mana.max))
        actor.mana.current = int(mana_payload.get("current", actor.mana.current))
        actor.mana.clamp()
    actor.magic_damage = int(payload.get("magic_damage", actor.magic_damage))
    actor.xp_to_level = int(payload.get("xp_to_level", actor.xp_to_level))
    spell_id = payload.get("spell_id")
    if spell_id:
        actor.spell_id = spell_id
        try:
            actor.current_spell = get_spell(spell_id)
        except KeyError:
            actor.current_spell = None
    equipment_payload = payload.get("equipment", {})
    if equipment_payload:
        actor.equipment = {}
        for slot, item_id in equipment_payload.items():
            try:
                item = get_item(item_id)
            except KeyError:
                continue
            actor.equipment[slot] = (item_id, item)
    actor.attack_profile.cooldown_s = float(
        attack_profile.get("cooldown_s", actor.attack_profile.cooldown_s)
    )
    actor.attack_profile.mp_gain_on_attack = int(
        attack_profile.get("mp_gain", actor.attack_profile.mp_gain_on_attack)
    )
    actor.attack_state.reset()
    actor.health.clamp()
    return actor


def _dt_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def create_default_state(
    slot_id: str,
    *,
    location_id: str | None = None,
) -> GameState:
    inventory = Inventory(keyblade_slots=3, armor_slots=10, accessory_slots=10)
    actors = build_party(DEFAULT_PARTY_TEMPLATES, inventory=inventory)
    selected_location = location_id or DEFAULT_LOCATION_ID
    return GameState(
        slot_id=slot_id,
        location_id=selected_location,
        inventory=inventory,
        actors=list(actors),
    )


def save_state(
    state: GameState,
    *,
    base_path: str | os.PathLike[str] | None = None,
) -> None:
    if not state.slot_id:
        raise ValueError("GameState.slot_id must be set before saving")
    now = _dt_now()
    if state.created_at is None:
        state.created_at = now
    state.updated_at = now
    payload = {
        "version": SAVE_VERSION,
        "slot_id": state.slot_id,
        "created_at": state.created_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
        "location_id": state.location_id,
        "inventory": _serialize_inventory(state.inventory),
        "actors": [_serialize_actor(actor) for actor in state.actors],
        "summary": {
            "party_names": [actor.name for actor in state.actors],
            "munny": int(state.inventory.munny),
        },
    }
    directory = _resolve_save_dir(base_path)
    _ensure_directory(directory)
    path = directory / f"{state.slot_id}{SAVE_FILE_SUFFIX}"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def load_state(
    slot_id: str,
    *,
    base_path: str | os.PathLike[str] | None = None,
) -> GameState | None:
    path = _slot_path(slot_id, base_path=base_path)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    inventory_payload = payload.get("inventory", {})
    actors_payload = payload.get("actors", [])
    inventory = _build_inventory(inventory_payload)
    actors = [_build_actor(entry) for entry in actors_payload]
    state = GameState(
        slot_id=slot_id,
        location_id=payload.get("location_id", DEFAULT_LOCATION_ID),
        inventory=inventory,
        actors=actors,
        created_at=_parse_datetime(payload.get("created_at")),
        updated_at=_parse_datetime(payload.get("updated_at")),
        summary=payload.get("summary", {}),
    )
    return state


def list_slots(
    *,
    max_slots: int = DEFAULT_MAX_SLOTS,
    base_path: str | os.PathLike[str] | None = None,
) -> List[SaveSlotInfo]:
    slots: List[SaveSlotInfo] = []
    for index in range(1, max_slots + 1):
        slot_id = f"slot{index}"
        info = SaveSlotInfo(
            slot_id=slot_id,
            title=f"Slot {index}",
            exists=False,
        )
        state = load_state(slot_id, base_path=base_path)
        if state is not None:
            info.exists = True
            info.updated_at = state.updated_at
            info.location_id = state.location_id
            info.party = state.summary.get("party_names") or [
                actor.name for actor in state.actors
            ]
            info.munny = int(state.summary.get("munny", state.inventory.munny))
        slots.append(info)
    return slots


__all__ = [
    "GameState",
    "SaveSlotInfo",
    "create_default_state",
    "save_state",
    "load_state",
    "list_slots",
    "DEFAULT_MAX_SLOTS",
]
