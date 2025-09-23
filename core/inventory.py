"""Inventory management for player items and equipment."""

from collections import defaultdict
from typing import Dict, List, Tuple

from core.items import get_item, Item
from core.materials import get_material


class Inventory:
    def __init__(
        self,
        keyblade_slots: int = 1,
        armor_slots: int = 1,
        accessory_slots: int = 1,
    ):
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
        # Munny (currency) held by the party; treat inventory as the ledger.
        self.munny: int = 0
        # Crafting materials tracked by identifier -> quantity owned.
        self.materials: Dict[str, int] = defaultdict(int)

    def add_munny(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Munny amount must be non-negative")
        self.munny += amount

    def spend_munny(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Munny amount must be non-negative")
        if amount > self.munny:
            raise ValueError("Insufficient munny")
        self.munny -= amount

    def add_item(self, item_id: str) -> None:
        item = get_item(item_id)
        slot = item.slot
        current = self.items_by_slot[slot]
        if len(current) >= self.capacity.get(slot, 0):
            raise ValueError(
                f"No free {slot} slots for item '{item_id}'"
            )
        current.append(item_id)
        self.item_list.append(item_id)

    def _ensure_equipment_slot(self, actor) -> Dict[str, Tuple[str, Item]]:
        """Return the actor equipment mapping, creating it when missing."""
        equipment = getattr(actor, "equipment", None)
        if equipment is None:
            equipment = {}
            actor.equipment = equipment
        return equipment

    def _apply_item_stats(
        self,
        actor,
        item: Item,
        *,
        remove: bool = False,
    ) -> None:
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
            raise ValueError(
                f"Item '{item_id}' not available in inventory"
            ) from exc
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
                # Restore removed item before raising to keep state consistent.
                slot_items.append(item_id)
                self.item_list.append(item_id)
                equipment[slot] = (prev_item_id, prev_item)
                raise ValueError(
                    f"No free {slot} slots to unequip '{prev_item_id}'"
                )
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

    # --- Material helpers -------------------------------------------------

    def add_material(self, material_id: str, amount: int = 1) -> None:
        if amount <= 0:
            raise ValueError("Material amount must be positive")
        get_material(material_id)  # Validate identifier.
        self.materials[material_id] += amount

    def material_count(self, material_id: str) -> int:
        return self.materials.get(material_id, 0)

    def has_materials(self, costs: Dict[str, int]) -> bool:
        return all(self.material_count(mid) >= qty for mid, qty in costs.items())

    def spend_materials(self, costs: Dict[str, int]) -> None:
        if not self.has_materials(costs):
            raise ValueError("Insufficient materials for synthesis")
        for material_id, qty in costs.items():
            if qty <= 0:
                continue
            self.materials[material_id] -= qty
            if self.materials[material_id] <= 0:
                self.materials.pop(material_id, None)

    def iter_materials(self):
        return self.materials.items()
