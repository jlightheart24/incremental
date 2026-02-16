export type Item = {
  name: string;
  slot: string;
  atk: number;
  defense: number;
  mp: number;
};

const KEY_DB: Record<string, Item> = {
  kingdom_key: { name: "Kingdom Key", slot: "keyblade", atk: 1, defense: 0, mp: 1 },
  mages_staff: { name: "Mage's Staff", slot: "keyblade", atk: 2, defense: 0, mp: 2 },
  knights_shield: { name: "Knight's Shield", slot: "keyblade", atk: 1, defense: 1, mp: 0 }
};

const ARMOR_DB: Record<string, Item> = {
  champion_belt: { name: "Champion Belt", slot: "armor", atk: 0, defense: 1, mp: 0 },
  heros_crest: { name: "Hero's Crest", slot: "armor", atk: 0, defense: 2, mp: 0 }
};

const ACCESSORY_DB: Record<string, Item> = {
  elven_bandana: { name: "Elven Bandana", slot: "accessory", atk: 0, defense: 1, mp: 0 }
};

const ITEM_DB: Record<string, Item> = { ...KEY_DB, ...ARMOR_DB, ...ACCESSORY_DB };

export function getItem(itemId: string): Item {
  const template = ITEM_DB[itemId];
  if (!template) throw new Error(`Unknown item '${itemId}'`);
  return { ...template };
}

export { ITEM_DB, KEY_DB, ARMOR_DB, ACCESSORY_DB };
