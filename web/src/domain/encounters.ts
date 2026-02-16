import { Enemy } from "./entities";

export type EnemyDrop = {
  itemId?: string;
  materialId?: string;
  chance: number;
  amount?: number;
};

export type EnemyDefinition = {
  name: string;
  hp: number;
  atk: number;
  defense: number;
  cd: number;
  portraitPath: string;
  xpReward: number;
  munnyReward: number;
  drops: EnemyDrop[];
};

export type EncounterTemplate = {
  enemyId?: string;
  level?: number;
  enemyLevel?: number;
  name?: string;
  hp?: number;
  atk?: number;
  defense?: number;
  cd?: number;
  portraitPath?: string;
  xpReward?: number;
  munnyReward?: number;
  goldReward?: number;
  drops?: EnemyDrop[];
};

export const ENEMY_DEFINITIONS: Record<string, EnemyDefinition> = {
  shadow: {
    name: "Shadow",
    hp: 22,
    atk: 2,
    defense: 1,
    cd: 2.5,
    portraitPath: "assets/portraits/enemies/shadow.png",
    xpReward: 12,
    munnyReward: 6,
    drops: [
      { materialId: "bright_shard", chance: 0.5, amount: 1 },
      { materialId: "dark_shard", chance: 0.4, amount: 1 }
    ]
  },
  soldier: {
    name: "Soldier",
    hp: 24,
    atk: 2,
    defense: 1,
    cd: 2.0,
    portraitPath: "assets/portraits/enemies/soldier.png",
    xpReward: 24,
    munnyReward: 12,
    drops: [
      { itemId: "champion_belt", chance: 0.25 },
      { materialId: "mythril_fragment", chance: 0.5, amount: 1 }
    ]
  }
};

export class EncounterPool {
  private pools: Record<string, EncounterTemplate[]> = {};
  private currentPool: string;
  private rng: () => number;
  private enemyDefinitions: Record<string, EnemyDefinition>;

  constructor(params: {
    pools: Record<string, EncounterTemplate[]>;
    defaultPool: string;
    enemyDefinitions?: Record<string, EnemyDefinition>;
    rng?: () => number;
  }) {
    const { pools, defaultPool, enemyDefinitions, rng } = params;
    if (!(defaultPool in pools)) {
      throw new Error(`Unknown enemy pool '${defaultPool}'`);
    }
    Object.entries(pools).forEach(([name, entries]) => {
      this.pools[name] = entries.map((entry) => ({ ...entry }));
    });
    this.currentPool = defaultPool;
    this.rng = rng ?? Math.random;
    this.enemyDefinitions = {};
    const defs = enemyDefinitions ?? ENEMY_DEFINITIONS;
    Object.entries(defs).forEach(([key, value]) => {
      this.enemyDefinitions[key] = { ...value, drops: [...value.drops] };
    });
  }

  getCurrentPool(): string {
    return this.currentPool;
  }

  setPool(poolName: string): void {
    if (!(poolName in this.pools)) {
      throw new Error(`Unknown enemy pool '${poolName}'`);
    }
    this.currentPool = poolName;
  }

  addEnemy(poolName: string, template: EncounterTemplate): void {
    this.pools[poolName] = this.pools[poolName] ?? [];
    this.pools[poolName].push({ ...template });
  }

  nextEnemy(): Enemy {
    const candidates = this.pools[this.currentPool];
    if (!candidates || candidates.length === 0) {
      throw new Error(`Enemy pool '${this.currentPool}' is empty`);
    }
    const template = { ...candidates[Math.floor(this.rng() * candidates.length)] };
    let merged: EncounterTemplate & Partial<EnemyDefinition>;
    if (template.enemyId) {
      const base = this.enemyDefinitions[template.enemyId];
      if (!base) throw new Error(`Encounter references unknown enemy id '${template.enemyId}'`);
      merged = { ...base, ...template };
    } else {
      merged = { ...template };
    }

    const xpReward = merged.xpReward ?? 0;
    const munnyReward = merged.munnyReward ?? merged.goldReward ?? 0;
    const drops = merged.drops ?? null;
    const level = Math.trunc(merged.level ?? merged.enemyLevel ?? 1) || 1;

    const enemy = new Enemy({
      name: merged.name,
      hp: merged.hp,
      atk: merged.atk,
      defense: merged.defense,
      cd: merged.cd,
      portraitPath: merged.portraitPath,
      xpReward,
      munnyReward,
      drops: drops ?? undefined,
      level
    });
    return enemy;
  }
}

export const DEFAULT_ENCOUNTER_POOLS: Record<string, EncounterTemplate[]> = {
  destiny_islands_beach: [
    { enemyId: "shadow", level: 1 },
    { enemyId: "soldier", level: 2 }
  ],
  destiny_islands_cove: [
    { enemyId: "shadow", level: 2, xpReward: 16, munnyReward: 10 },
    {
      enemyId: "soldier",
      level: 3,
      xpReward: 32,
      munnyReward: 18,
      drops: [
        { itemId: "champion_belt", chance: 0.4 },
        { materialId: "mythril_fragment", chance: 0.65, amount: 1 }
      ]
    }
  ],
  traverse_town_first_district: [
    { enemyId: "shadow", level: 3, xpReward: 22, munnyReward: 14 },
    {
      enemyId: "soldier",
      level: 4,
      xpReward: 36,
      munnyReward: 22,
      drops: [{ materialId: "mythril_fragment", chance: 0.6, amount: 1 }]
    }
  ],
  traverse_town_second_district: [
    { enemyId: "soldier", level: 5, xpReward: 44, munnyReward: 28 },
    {
      enemyId: "soldier",
      level: 6,
      xpReward: 48,
      munnyReward: 32,
      drops: [{ itemId: "champion_belt", chance: 0.35 }]
    }
  ]
};
