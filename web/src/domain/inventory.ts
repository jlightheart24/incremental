import { Item, getItem } from "./items";
import { ItemLevelRequirement, maxLevel, requirementForLevel } from "./item_levels";
import { getMaterial } from "./materials";
import { Actor } from "./entities";

export class Inventory {
  capacity: Record<string, number>;
  itemsBySlot: Record<string, string[]>;
  itemList: string[];
  munny: number;
  materials: Record<string, number>;
  itemLevels: Record<string, number>;

  constructor(params: { keybladeSlots?: number; armorSlots?: number; accessorySlots?: number } = {}) {
    this.capacity = {
      keyblade: Math.trunc(params.keybladeSlots ?? 1),
      armor: Math.trunc(params.armorSlots ?? 1),
      accessory: Math.trunc(params.accessorySlots ?? 1)
    };
    this.itemsBySlot = {};
    this.itemList = [];
    this.munny = 0;
    this.materials = {};
    this.itemLevels = {};
  }

  addMunny(amount: number): void {
    if (amount < 0) throw new Error("Munny amount must be non-negative");
    this.munny += Math.trunc(amount);
  }

  spendMunny(amount: number): void {
    if (amount < 0) throw new Error("Munny amount must be non-negative");
    if (amount > this.munny) throw new Error("Insufficient munny");
    this.munny -= Math.trunc(amount);
  }

  addItem(itemId: string): void {
    const item = this.leveledItem(itemId);
    const slot = item.slot;
    const current = this.itemsBySlot[slot] ?? [];
    if (current.length >= (this.capacity[slot] ?? 0)) {
      throw new Error(`No free ${slot} slots for item '${itemId}'`);
    }
    current.push(itemId);
    this.itemsBySlot[slot] = current;
    this.itemList.push(itemId);
  }

  private ensureEquipmentSlot(actor: Actor): Record<string, { itemId: string; item: Item }> {
    if (!actor.equipment) actor.equipment = {};
    return actor.equipment as Record<string, { itemId: string; item: Item }>;
  }

  private applyItemStats(actor: Actor, item: Item, remove = false): void {
    const multiplier = remove ? -1 : 1;
    actor.stats.atk += multiplier * Math.trunc(item.atk);
    actor.stats.defense += multiplier * Math.trunc(item.defense);
    actor.stats.mpMax += multiplier * Math.trunc(item.mp);
    actor.mana.max += multiplier * Math.trunc(item.mp);
    actor.mana.clamp();
  }

  equipItem(actor: Actor, itemId: string): void {
    const item = getItem(itemId);
    const slot = item.slot;
    const slotItems = this.itemsBySlot[slot] ?? [];
    const index = slotItems.indexOf(itemId);
    if (index === -1) throw new Error(`Item '${itemId}' not available in inventory`);
    slotItems.splice(index, 1);
    const listIndex = this.itemList.indexOf(itemId);
    if (listIndex !== -1) this.itemList.splice(listIndex, 1);

    const equipment = this.ensureEquipmentSlot(actor);
    if (equipment[slot]) {
      const prev = equipment[slot];
      if ((this.itemsBySlot[slot] ?? []).length >= (this.capacity[slot] ?? 0)) {
        slotItems.push(itemId);
        this.itemList.push(itemId);
        equipment[slot] = prev;
        throw new Error(`No free ${slot} slots to unequip '${prev.itemId}'`);
      }
      this.itemsBySlot[slot] = this.itemsBySlot[slot] ?? [];
      this.itemsBySlot[slot].push(prev.itemId);
      this.itemList.push(prev.itemId);
      this.applyItemStats(actor, prev.item, true);
    }

    this.applyItemStats(actor, item, false);
    equipment[slot] = { itemId, item };
  }

  unequipSlot(actor: Actor, slot: string): void {
    const equipment = actor.equipment as Record<string, { itemId: string; item: Item }> | undefined;
    if (!equipment || !equipment[slot]) return;

    const capacity = this.capacity[slot] ?? 0;
    const slotItems = this.itemsBySlot[slot] ?? [];
    if (slotItems.length >= capacity) throw new Error(`No free ${slot} slots to store unequipped item`);

    const entry = equipment[slot];
    delete equipment[slot];
    slotItems.push(entry.itemId);
    this.itemsBySlot[slot] = slotItems;
    this.itemList.push(entry.itemId);
    this.applyItemStats(actor, entry.item, true);
  }

  addMaterial(materialId: string, amount = 1): void {
    if (amount <= 0) throw new Error("Material amount must be positive");
    getMaterial(materialId);
    this.materials[materialId] = (this.materials[materialId] ?? 0) + Math.trunc(amount);
  }

  materialCount(materialId: string): number {
    return this.materials[materialId] ?? 0;
  }

  hasMaterials(costs: Record<string, number>): boolean {
    return Object.entries(costs).every(([id, qty]) => this.materialCount(id) >= qty);
  }

  spendMaterials(costs: Record<string, number>): void {
    if (!this.hasMaterials(costs)) throw new Error("Insufficient materials for synthesis");
    Object.entries(costs).forEach(([id, qty]) => {
      if (qty <= 0) return;
      this.materials[id] = (this.materials[id] ?? 0) - qty;
      if (this.materials[id] <= 0) delete this.materials[id];
    });
  }

  iterMaterials(): [string, number][] {
    return Object.entries(this.materials);
  }

  itemLevel(itemId: string): number {
    const level = this.itemLevels[itemId] ?? 1;
    return level > 0 ? level : 1;
  }

  setItemLevel(itemId: string, level: number): void {
    if (level <= 0) throw new Error("Item level must be positive");
    if (level === 1) delete this.itemLevels[itemId];
    else this.itemLevels[itemId] = level;
  }

  iterItemLevels(): [string, number][] {
    return Object.entries(this.itemLevels);
  }

  leveledItemAtLevel(itemId: string, level: number): Item {
    const item = getItem(itemId);
    const adjustedLevel = Math.max(level, 1);
    if (adjustedLevel <= 1) return item;
    const bonus = adjustedLevel - 1;
    (['atk', 'defense', 'mp'] as const).forEach((attr) => {
      const currentValue = item[attr] ?? 0;
      if (currentValue > 0) item[attr] = currentValue + bonus;
    });
    return item;
  }

  leveledItem(itemId: string): Item {
    return this.leveledItemAtLevel(itemId, this.itemLevel(itemId));
  }

  itemCount(itemId: string): number {
    return this.itemList.filter((entry) => entry === itemId).length;
  }

  nextLevelRequirement(itemId: string): ItemLevelRequirement | null {
    const currentLevel = this.itemLevel(itemId);
    const targetLevel = currentLevel + 1;
    if (targetLevel > maxLevel(itemId)) return null;
    return requirementForLevel(itemId, targetLevel);
  }

  canLevelItem(itemId: string): boolean {
    const requirement = this.nextLevelRequirement(itemId);
    if (!requirement) return false;
    if (this.itemCount(itemId) < requirement.itemCost) return false;
    return this.hasMaterials(requirement.materials);
  }

  levelUpItem(itemId: string): ItemLevelRequirement {
    const requirement = this.nextLevelRequirement(itemId);
    if (!requirement) throw new Error("Item is already at max level");
    if (this.itemCount(itemId) < requirement.itemCost) throw new Error("Not enough duplicate items to level up");
    if (!this.hasMaterials(requirement.materials)) throw new Error("Missing required materials");

    this.consumeItems(itemId, requirement.itemCost);
    this.spendMaterials(requirement.materials);
    const newLevel = this.itemLevel(itemId) + 1;
    this.setItemLevel(itemId, newLevel);
    return requirement;
  }

  private consumeItems(itemId: string, amount: number): void {
    if (amount <= 0) return;
    const slot = getItem(itemId).slot;
    const slotItems = this.itemsBySlot[slot] ?? [];
    let removed = 0;
    while (removed < amount) {
      const index = slotItems.indexOf(itemId);
      if (index === -1) break;
      slotItems.splice(index, 1);
      removed += 1;
    }
    for (let i = 0; i < removed; i += 1) {
      const listIndex = this.itemList.indexOf(itemId);
      if (listIndex === -1) break;
      this.itemList.splice(listIndex, 1);
    }
  }
}
