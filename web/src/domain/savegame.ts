import { Actor } from "./entities";
import { Inventory } from "./inventory";
import { DEFAULT_LOCATION_ID, getLocation } from "./locations";
import { getItem } from "./items";
import { getSpell } from "./spells";
import { buildParty, DEFAULT_PARTY_TEMPLATES } from "./party";

export const SAVE_VERSION = 2;
export const DEFAULT_MAX_SLOTS = 3;
const SAVE_KEY_PREFIX = "incremental_save:";

export type SaveSlotInfo = {
  slotId: string;
  title: string;
  exists: boolean;
  updatedAt?: Date | null;
  locationId?: string | null;
  party: string[];
  munny: number;
  locationDisplay: () => string;
};

export type GameState = {
  slotId: string;
  locationId: string;
  inventory: Inventory;
  actors: Actor[];
  createdAt?: Date | null;
  updatedAt?: Date | null;
  summary: Record<string, unknown>;
};

export type StorageLike = {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
};

export class MemoryStorage implements StorageLike {
  private store = new Map<string, string>();

  getItem(key: string): string | null {
    return this.store.has(key) ? (this.store.get(key) ?? null) : null;
  }

  setItem(key: string, value: string): void {
    this.store.set(key, value);
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }
}

function defaultStorage(): StorageLike {
  if (typeof window !== "undefined" && window.localStorage) {
    return window.localStorage;
  }
  return new MemoryStorage();
}

function slotKey(slotId: string): string {
  return `${SAVE_KEY_PREFIX}${slotId}`;
}

function serializeInventory(inventory: Inventory): Record<string, unknown> {
  return {
    capacity: { ...inventory.capacity },
    items_by_slot: Object.fromEntries(
      Object.entries(inventory.itemsBySlot).map(([slot, items]) => [slot, [...items]])
    ),
    item_list: [...inventory.itemList],
    munny: Math.trunc(inventory.munny),
    materials: { ...inventory.materials },
    item_levels: Object.fromEntries(
      Object.entries(inventory.itemLevels).filter(([, level]) => level > 1)
    )
  };
}

function serializeActor(actor: Actor): Record<string, unknown> {
  const equipment: Record<string, string> = {};
  if (actor.equipment) {
    Object.entries(actor.equipment).forEach(([slot, entry]) => {
      if (entry && typeof entry === "object" && "itemId" in entry) {
        equipment[slot] = (entry as { itemId: string }).itemId;
      }
    });
  }
  return {
    name: actor.name,
    portrait_path: actor.portraitPath,
    stats: {
      max_hp: actor.stats.maxHp,
      atk: actor.stats.atk,
      defense: actor.stats.defense,
      speed: actor.stats.speed,
      mp_max: actor.stats.mpMax
    },
    health: {
      current: actor.health.current,
      max: actor.health.max
    },
    mana: {
      current: actor.mana?.current ?? 0,
      max: actor.mana?.max ?? 0
    },
    magic_damage: actor.magicDamage ?? 0,
    level: actor.level ?? 1,
    xp: actor.xp ?? 0,
    xp_to_level: actor.xpToLevel ?? 0,
    spell_id: actor.spellId ?? null,
    attack_profile: {
      cooldown_s: actor.attackProfile.cooldownS,
      mp_gain: actor.attackProfile.mpGainOnAttack
    },
    equipment
  };
}

function buildInventory(payload: Record<string, unknown>): Inventory {
  const capacity = (payload.capacity as Record<string, number>) ?? {};
  const inventory = new Inventory({
    keybladeSlots: toNumber(capacity.keyblade, 0),
    armorSlots: toNumber(capacity.armor, 0),
    accessorySlots: toNumber(capacity.accessory, 0)
  });

  inventory.itemsBySlot = {};
  const itemsBySlot = (payload.items_by_slot as Record<string, string[]>) ?? {};
  Object.entries(itemsBySlot).forEach(([slot, items]) => {
    inventory.itemsBySlot[slot] = [...items];
  });

  inventory.itemList = [...((payload.item_list as string[]) ?? [])];
  inventory.munny = toNumber(payload.munny, 0);
  inventory.materials = { ...((payload.materials as Record<string, number>) ?? {}) };

  const itemLevelsPayload = (payload.item_levels as Record<string, number>) ?? {};
  inventory.itemLevels = {};
  Object.entries(itemLevelsPayload).forEach(([itemId, level]) => {
    const converted = toNumber(level, 0);
    if (converted > 1) inventory.itemLevels[itemId] = converted;
  });

  return inventory;
}

function buildActor(payload: Record<string, unknown>, inventory?: Inventory | null): Actor {
  const stats = (payload.stats as Record<string, unknown>) ?? {};
  const attackProfile = (payload.attack_profile as Record<string, unknown>) ?? {};
  const manaPayload = (payload.mana as Record<string, unknown>) ?? {};
  const healthPayload = (payload.health as Record<string, unknown>) ?? {};

  const actor = new Actor(String(payload.name ?? "Actor"), {
    hp: toNumber(stats.max_hp, 10),
    atk: toNumber(stats.atk, 5),
    defense: toNumber(stats.defense, 1),
    speed: toNumber(stats.speed, 1),
    mpMax: toNumber(stats.mp_max, toNumber(manaPayload.max, 10)),
    cd: toNumber(attackProfile.cooldown_s, 0.2),
    mpGain: toNumber(attackProfile.mp_gain, 1),
    portraitPath: (payload.portrait_path as string | null | undefined) ?? null,
    level: toNumber(payload.level, 1),
    xp: toNumber(payload.xp, 0),
    spellId: null
  });

  actor.health.max = toNumber(healthPayload.max, actor.health.max);
  actor.health.current = toNumber(healthPayload.current, actor.health.current);
  actor.mana.max = toNumber(manaPayload.max, actor.mana.max);
  actor.mana.current = toNumber(manaPayload.current, actor.mana.current);
  actor.mana.clamp();
  actor.magicDamage = toNumber(payload.magic_damage, actor.magicDamage);
  actor.xpToLevel = toNumber(payload.xp_to_level, actor.xpToLevel);

  const spellId = payload.spell_id as string | null | undefined;
  if (spellId) {
    actor.spellId = spellId;
    try {
      actor.currentSpell = getSpell(spellId);
    } catch {
      actor.currentSpell = null;
    }
  }

  const equipmentPayload = (payload.equipment as Record<string, string>) ?? {};
  if (Object.keys(equipmentPayload).length > 0) {
    actor.equipment = {};
    Object.entries(equipmentPayload).forEach(([slot, itemId]) => {
      try {
        const item = inventory ? inventory.leveledItem(itemId) : getItem(itemId);
        actor.equipment[slot] = { itemId, item };
      } catch {
        return;
      }
    });
  }

  actor.attackProfile.cooldownS = toNumber(attackProfile.cooldown_s, actor.attackProfile.cooldownS);
  actor.attackProfile.mpGainOnAttack = toNumber(
    attackProfile.mp_gain,
    actor.attackProfile.mpGainOnAttack
  );
  actor.attackState.reset();
  actor.health.clamp();
  return actor;
}

function nowIsoSeconds(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function parseDate(value: unknown): Date | null {
  if (typeof value !== "string" || !value) return null;
  const dt = new Date(value);
  return Number.isNaN(dt.getTime()) ? null : dt;
}

export function createDefaultState(slotId: string, params: { locationId?: string | null } = {}): GameState {
  const inventory = new Inventory({ keybladeSlots: 3, armorSlots: 10, accessorySlots: 10 });
  const actors = buildParty(DEFAULT_PARTY_TEMPLATES, inventory);
  const selectedLocation = params.locationId ?? DEFAULT_LOCATION_ID;
  return {
    slotId,
    locationId: selectedLocation,
    inventory,
    actors: [...actors],
    summary: {}
  };
}

export function saveState(
  state: GameState,
  params: { storage?: StorageLike } = {}
): void {
  if (!state.slotId) throw new Error("GameState.slotId must be set before saving");
  const nowIso = nowIsoSeconds();
  if (!state.createdAt) state.createdAt = new Date(nowIso);
  state.updatedAt = new Date(nowIso);

  const payload = {
    version: SAVE_VERSION,
    slot_id: state.slotId,
    created_at: state.createdAt.toISOString(),
    updated_at: state.updatedAt.toISOString(),
    location_id: state.locationId,
    inventory: serializeInventory(state.inventory),
    actors: state.actors.map((actor) => serializeActor(actor)),
    summary: {
      party_names: state.actors.map((actor) => actor.name),
      munny: Math.trunc(state.inventory.munny)
    }
  };

  const storage = params.storage ?? defaultStorage();
  storage.setItem(slotKey(state.slotId), JSON.stringify(payload, null, 2));
}

export function loadState(
  slotId: string,
  params: { storage?: StorageLike } = {}
): GameState | null {
  const storage = params.storage ?? defaultStorage();
  const raw = storage.getItem(slotKey(slotId));
  if (!raw) return null;
  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
  const inventoryPayload = (payload.inventory as Record<string, unknown>) ?? {};
  const actorsPayload = (payload.actors as Record<string, unknown>[]) ?? [];
  const inventory = buildInventory(inventoryPayload);
  const actors = actorsPayload.map((entry) => buildActor(entry, inventory));

  return {
    slotId,
    locationId: String(payload.location_id ?? DEFAULT_LOCATION_ID),
    inventory,
    actors,
    createdAt: parseDate(payload.created_at),
    updatedAt: parseDate(payload.updated_at),
    summary: (payload.summary as Record<string, unknown>) ?? {}
  };
}

export function listSlots(
  params: { maxSlots?: number; storage?: StorageLike } = {}
): SaveSlotInfo[] {
  const maxSlots = params.maxSlots ?? DEFAULT_MAX_SLOTS;
  const storage = params.storage ?? defaultStorage();
  const slots: SaveSlotInfo[] = [];

  for (let index = 1; index <= maxSlots; index += 1) {
    const slotId = `slot${index}`;
    const info: SaveSlotInfo = {
      slotId,
      title: `Slot ${index}`,
      exists: false,
      updatedAt: null,
      locationId: null,
      party: [],
      munny: 0,
      locationDisplay: () => {
        if (!info.locationId) return "Unknown";
        try {
          const location = getLocation(info.locationId);
          return location.title;
        } catch {
          return info.locationId ?? "Unknown";
        }
      }
    };

    const state = loadState(slotId, { storage });
    if (state) {
      info.exists = true;
      info.updatedAt = state.updatedAt ?? null;
      info.locationId = state.locationId;
      const summaryParty = (state.summary.party_names as string[] | undefined) ?? null;
      info.party = summaryParty ?? state.actors.map((actor) => actor.name);
      info.munny = toNumber(state.summary.munny, state.inventory.munny);
    }

    slots.push(info);
  }

  return slots;
}

function toNumber(value: unknown, fallback: number): number {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}
