"""Item definitions and lookup helpers."""

from typing import Dict
import copy


class Item:
    """Simple data container describing equippable items."""

    __slots__ = ("name", "slot", "atk", "defense", "mp")

    def __init__(self, name: str, slot: str, *, atk: int = 0, defense: int = 0, mp: int = 0) -> None:
        self.name = str(name)
        self.slot = str(slot)
        self.atk = int(atk)
        self.defense = int(defense)
        self.mp = int(mp)

    def __repr__(self) -> str:
        return (
            f"Item(name={self.name!r}, slot={self.slot!r}, "
            f"atk={self.atk}, defense={self.defense}, mp={self.mp})"
        )


KEY_DB: Dict[str, Item] = {
    "kingdom_key": Item("Kingdom Key", "keyblade", atk=1, mp=1),
    "mages_staff": Item("Mage's Staff", "keyblade", atk=2, mp=2),
    "knights_shield": Item("Knight's Shield", "keyblade", atk=1, defense=1),
}

ARMOR_DB: Dict[str, Item] = {
    "champion_belt": Item("Champion Belt", "armor", defense=1),
    "heros_crest": Item("Hero's Crest", "armor", defense=2),
}

ACCESSORY_DB: Dict[str, Item] = {
    "elven_bandana": Item("Elven Bandana", "accessory", defense=1),
}

ITEM_DB: Dict[str, Item] = {**KEY_DB, **ARMOR_DB, **ACCESSORY_DB}


def get_item(item_id: str) -> Item:
    try:
        template = ITEM_DB[item_id]
    except KeyError as exc:
        raise KeyError(f"Unknown item '{item_id}'") from exc
    return copy.deepcopy(template)
