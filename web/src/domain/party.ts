import { Actor } from "./entities";
import { Inventory } from "./inventory";

function resolvePortraitPath(value: string | string[] | null | undefined): string | null {
  if (!value) return null;
  if (Array.isArray(value)) return value.join("/");
  return value;
}

export function buildParty(
  templates: Array<Record<string, unknown>>,
  inventory?: Inventory | null
): Actor[] {
  const party: Actor[] = [];
  templates.forEach((template) => {
    const data = { ...template };
    const name = String(data.name ?? "Actor");
    delete data.name;

    const loadout = (data.loadout as string[] | undefined) ?? [];
    delete data.loadout;

    const portraitPath = resolvePortraitPath(data.portrait_path as string | string[] | null | undefined);
    delete data.portrait_path;

    const spellId = (data.spell_id as string | null | undefined) ?? null;
    delete data.spell_id;

    const actor = new Actor(name, {
      hp: toNumber(data.hp, 10),
      atk: toNumber(data.atk, 5),
      defense: toNumber(data.defense, 1),
      speed: toNumber(data.speed, 1),
      mpMax: toNumber(data.mp_max, 10),
      cd: toNumber(data.cd, 0.2),
      mpGain: toNumber(data.mp_gain, 1),
      portraitPath,
      level: toNumber(data.level, 1),
      xp: toNumber(data.xp, 0),
      spellId
    });

    loadout.forEach((itemId) => {
      if (inventory) {
        inventory.addItem(itemId);
        inventory.equipItem(actor, itemId);
      }
    });
    party.push(actor);
  });

  return party;
}

export const DEFAULT_PARTY_TEMPLATES: Array<Record<string, unknown>> = [
  {
    name: "Sora",
    cd: 0.2,
    atk: 5,
    portrait_path: ["assets", "portraits", "sora.png"],
    spell_id: "fire",
    loadout: ["kingdom_key"]
  },
  {
    name: "Donald",
    cd: 0.3,
    atk: 4,
    portrait_path: ["assets", "portraits", "donald.png"],
    spell_id: "blizzard",
    loadout: ["mages_staff"]
  },
  {
    name: "Goofy",
    cd: 0.4,
    atk: 3,
    portrait_path: ["assets", "portraits", "goofy.png"],
    spell_id: "thunder",
    loadout: ["knights_shield"]
  }
];

function toNumber(value: unknown, fallback: number): number {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}
