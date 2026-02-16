import { AttackProfile, AttackState } from "./attack";
import { Health, Mana, Stats } from "./stats";
import { Spell, getSpell } from "./spells";

export class Character {
  name: string;
  portraitPath: string | null;
  stats: Stats;
  health: Health;
  attackProfile: AttackProfile;
  attackState: AttackState;

  constructor(
    name: string,
    params: {
      hp?: number;
      atk?: number;
      defense?: number;
      speed?: number;
      mpMax?: number;
      cd?: number;
      mpGain?: number;
      portraitPath?: string | null;
    } = {}
  ) {
    const hp = params.hp ?? 10;
    const atk = params.atk ?? 5;
    const defense = params.defense ?? 1;
    const speed = params.speed ?? 1;
    const mpMax = params.mpMax ?? 10;
    const cd = params.cd ?? 0.2;
    const mpGain = params.mpGain ?? 0;

    this.name = name;
    this.portraitPath = params.portraitPath ?? null;
    this.stats = new Stats({ maxHp: hp, atk, defense, speed, mpMax });
    this.health = new Health({ current: hp, max: hp });
    this.attackProfile = new AttackProfile({
      cooldownS: cd,
      mpGainOnAttack: mpGain
    });
    this.attackState = new AttackState();
  }

  toString(): string {
    return `${this.name}(HP=${this.health.current})`;
  }
}

export class Actor extends Character {
  mana: Mana;
  level: number;
  xp: number;
  xpToLevel: number;
  magicDamage: number;
  currentSpell: Spell | null;
  spellId: string | null;
  equipment: Record<string, { itemId: string; item: unknown }>;

  constructor(
    name: string,
    params: {
      hp?: number;
      atk?: number;
      defense?: number;
      speed?: number;
      mpMax?: number;
      cd?: number;
      mpGain?: number;
      portraitPath?: string | null;
      level?: number;
      xp?: number;
      spellId?: string | null;
    } = {}
  ) {
    super(name, params);
    const mpMax = params.mpMax ?? 10;

    this.mana = new Mana({ current: 0, max: mpMax });
    this.level = params.level ?? 1;
    this.xp = params.xp ?? 0;
    this.xpToLevel = 100 + (this.level - 1) * 50;
    this.magicDamage = 12;
    this.currentSpell = null;
    this.spellId = null;
    if (params.spellId) {
      this.setSpell(params.spellId);
    }
    this.equipment = {};
  }

  gainXp(amount: number): void {
    this.xp += Math.trunc(amount);
    while (this.xp >= this.xpToLevel) {
      this.xp -= this.xpToLevel;
      this.level += 1;
      this.stats.maxHp += 5;
      this.stats.atk += 2;
      this.stats.defense += 1;
      this.stats.speed += 1;
      this.stats.mpMax += 2;
      this.health.max += 5;
      this.health.current = this.health.max;
      this.xpToLevel = 100 + (this.level - 1) * 50;
    }
  }

  setSpell(spellId: string | null): void {
    if (!spellId) {
      this.spellId = null;
      this.currentSpell = null;
      return;
    }
    const spell = getSpell(spellId);
    this.spellId = spellId;
    this.currentSpell = spell;
    this.magicDamage = spell.damage;
    this.stats.mpMax = spell.mpMax;
    this.mana.max = spell.mpMax;
    this.mana.clamp();
  }

  toString(): string {
    return `${this.name}(HP=${this.health.current}, MP=${this.mana.current})`;
  }
}

export class Enemy extends Character {
  level: number;
  xpReward: number;
  munnyReward: number;
  drops: unknown[];
  private baseStats: { hp: number; atk: number; defense: number; speed: number };

  constructor(params: {
    name?: string;
    hp?: number;
    atk?: number;
    defense?: number;
    speed?: number;
    mpMax?: number;
    cd?: number;
    mpGain?: number;
    portraitPath?: string | null;
    xpReward?: number;
    munnyReward?: number;
    drops?: unknown[] | null;
    level?: number;
  } = {}) {
    super(params.name ?? "Enemy", {
      hp: params.hp ?? 20,
      atk: params.atk ?? 3,
      defense: params.defense ?? 2,
      speed: params.speed ?? 1,
      mpMax: params.mpMax ?? 0,
      cd: params.cd ?? 0.8,
      mpGain: params.mpGain ?? 0,
      portraitPath: params.portraitPath ?? null
    });

    this.level = Math.max(1, Math.trunc(params.level ?? 1));
    this.baseStats = {
      hp: Math.trunc(params.hp ?? 20),
      atk: Math.trunc(params.atk ?? 3),
      defense: Math.trunc(params.defense ?? 2),
      speed: Math.trunc(params.speed ?? 1)
    };
    this.xpReward = Math.trunc(params.xpReward ?? 50);
    this.munnyReward = Math.trunc(params.munnyReward ?? 0);
    this.drops = params.drops ? [...params.drops] : [];
    this.applyLevelScaling();
  }

  toString(): string {
    return `${this.name}(Lv${this.level} HP=${this.health.current})`;
  }

  private applyLevelScaling(): void {
    if (this.level <= 1) return;
    const multiplier = Number(this.level);
    const scale = (value: number): number =>
      Math.max(1, Math.trunc(Math.round(value * multiplier)));

    this.stats.maxHp = scale(this.baseStats.hp);
    this.health.max = this.stats.maxHp;
    this.health.current = this.health.max;
    this.stats.atk = scale(this.baseStats.atk);
    this.stats.defense = scale(this.baseStats.defense);
    this.stats.speed = scale(this.baseStats.speed);
  }
}
