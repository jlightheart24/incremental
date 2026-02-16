export type Spell = {
  spellId: string;
  name: string;
  mpMax: number;
  damage: number;
};

const SPELL_BOOK: Record<string, Spell> = {
  fire: { spellId: "fire", name: "Fire", mpMax: 10, damage: 18 },
  blizzard: { spellId: "blizzard", name: "Blizzard", mpMax: 14, damage: 24 },
  thunder: { spellId: "thunder", name: "Thunder", mpMax: 12, damage: 20 }
};

export function getSpell(spellId: string): Spell {
  const spell = SPELL_BOOK[spellId];
  if (!spell) throw new Error(`Unknown spell '${spellId}'`);
  return spell;
}

export function spellIds(): string[] {
  return Object.keys(SPELL_BOOK);
}

export function defaultSpell(): Spell {
  const values = Object.values(SPELL_BOOK);
  if (!values.length) throw new Error("Spell book is empty");
  return values[0];
}

export { SPELL_BOOK };
