"""Inventory management for player items and equipment."""

from collections import defaultdict
from typing import Dict, List, Tuple

from core.items import get_item, Item


class Inventory:
    def __init__(self, keyblade_slots: int = 1, armor_slots: int = 1, accessory_slots: int = 1):
        # Maximum number of unequipped items we can store per slot type.
        self.capacity: Dict[str, int] = {
            "keyblade": int(keyblade_slots),
            "armor": int(armor_slots),
            "accessory": int(accessory_slots),
        }
        # Items owned, grouped by slot type.
        self.items_by_slot: Dict[str, List[str]] = defaultdict(list)
        # Optional flat list for iteration or UI display.
        self.item_list: List[str] = []

    def add_item(self, item_id: str) -> None:
        item = get_item(item_id)
        slot = item.slot
        current = self.items_by_slot[slot]
        if len(current) >= self.capacity.get(slot, 0):
            raise ValueError(f"No free {slot} slots for item '{item_id}'")
        current.append(item_id)
        self.item_list.append(item_id)

    def _ensure_equipment_slot(self, actor) -> Dict[str, Tuple[str, Item]]:
        """Return the actor equipment mapping, creating it when missing."""
        equipment = getattr(actor, "equipment", None)
        if equipment is None:
            equipment = {}
            actor.equipment = equipment
        return equipment

    def _apply_item_stats(self, actor, item: Item, *, remove: bool = False) -> None:
        multiplier = -1 if remove else 1
        actor.stats.atk += multiplier * int(item.atk)
        actor.stats.defense += multiplier * int(item.defense)
        actor.stats.mp_max += multiplier * int(item.mp)
        actor.mana.max += multiplier * int(item.mp)
        actor.mana.clamp()

    def equip_item(self, actor, item_id: str) -> None:
        item = get_item(item_id)
        slot = item.slot
        slot_items = self.items_by_slot[slot]
        try:
            slot_items.remove(item_id)
        except ValueError as exc:
            raise ValueError(f"Item '{item_id}' not available in inventory") from exc
        try:
            self.item_list.remove(item_id)
        except ValueError:
            # Keep state consistent if item_list was desynced; continue.
            pass

        equipment = self._ensure_equipment_slot(actor)
        if slot in equipment:
            # Re-add previously equipped item before replacing it.
            prev_item_id, prev_item = equipment.pop(slot)
            if len(self.items_by_slot[slot]) >= self.capacity.get(slot, 0):
                # Restore removed item before raising so state stays consistent.
                slot_items.append(item_id)
                self.item_list.append(item_id)
                equipment[slot] = (prev_item_id, prev_item)
                raise ValueError(f"No free {slot} slots to unequip '{prev_item_id}'")
            self.items_by_slot[slot].append(prev_item_id)
            self.item_list.append(prev_item_id)
            self._apply_item_stats(actor, prev_item, remove=True)

        self._apply_item_stats(actor, item)
        equipment[slot] = (item_id, item)

    def unequip_slot(self, actor, slot: str) -> None:
        equipment = getattr(actor, "equipment", None)
        if not equipment or slot not in equipment:
            return

        capacity = self.capacity.get(slot, 0)
        slot_items = self.items_by_slot[slot]
        if len(slot_items) >= capacity:
            raise ValueError(f"No free {slot} slots to store unequipped item")

        item_id, item = equipment.pop(slot)
        slot_items.append(item_id)
        self.item_list.append(item_id)
        self._apply_item_stats(actor, item, remove=True)
