"""Inventory management for player items and equipment."""

from collections import defaultdict
from typing import Dict, List, Tuple

from core.data.items import get_item, Item
from core.data.item_levels import ItemLevelRequirement, max_level, requirement_for_level
from core.data.materials import get_material


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
        # Persistent item levels keyed by item identifier.
        self.item_levels: Dict[str, int] = {}

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
        item = self.leveled_item(item_id)
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

    # --- Item level helpers -----------------------------------------------

    def item_level(self, item_id: str) -> int:
        level = self.item_levels.get(item_id, 1)
        return level if level > 0 else 1

    def set_item_level(self, item_id: str, level: int) -> None:
        if level <= 0:
            raise ValueError("Item level must be positive")
        if level == 1:
            self.item_levels.pop(item_id, None)
        else:
            self.item_levels[item_id] = level

    def iter_item_levels(self):
        return self.item_levels.items()

    def leveled_item_at_level(self, item_id: str, level: int) -> Item:
        item = get_item(item_id)
        adjusted_level = max(level, 1)
        if adjusted_level <= 1:
            return item
        bonus = adjusted_level - 1
        for attr in ("atk", "defense", "mp"):
            current_value = getattr(item, attr, 0)
            if current_value > 0:
                setattr(item, attr, current_value + bonus)
        return item

    def leveled_item(self, item_id: str) -> Item:
        return self.leveled_item_at_level(item_id, self.item_level(item_id))

    def item_count(self, item_id: str) -> int:
        return self.item_list.count(item_id)

    def next_level_requirement(self, item_id: str) -> ItemLevelRequirement | None:
        current_level = self.item_level(item_id)
        target_level = current_level + 1
        if target_level > max_level(item_id):
            return None
        return requirement_for_level(item_id, target_level)

    def can_level_item(self, item_id: str) -> bool:
        requirement = self.next_level_requirement(item_id)
        if requirement is None:
            return False
        if self.item_count(item_id) < requirement.item_cost:
            return False
        return self.has_materials(requirement.materials)

    def level_up_item(self, item_id: str) -> ItemLevelRequirement:
        requirement = self.next_level_requirement(item_id)
        if requirement is None:
            raise ValueError("Item is already at max level")
        if self.item_count(item_id) < requirement.item_cost:
            raise ValueError("Not enough duplicate items to level up")
        if not self.has_materials(requirement.materials):
            raise ValueError("Missing required materials")

        self._consume_items(item_id, requirement.item_cost)
        self.spend_materials(requirement.materials)
        new_level = self.item_level(item_id) + 1
        self.set_item_level(item_id, new_level)
        return requirement

    def _consume_items(self, item_id: str, amount: int) -> None:
        if amount <= 0:
            return
        slot = get_item(item_id).slot
        slot_items = self.items_by_slot.get(slot, [])
        removed = 0
        while removed < amount:
            try:
                slot_items.remove(item_id)
            except ValueError:
                break
            removed += 1
        for _ in range(removed):
            try:
                self.item_list.remove(item_id)
            except ValueError:
                break
