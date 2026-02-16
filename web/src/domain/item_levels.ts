export type ItemLevelRequirement = {
  level: number;
  itemCost: number;
  materials: Record<string, number>;
};

const ITEM_LEVEL_TABLE: Record<string, ItemLevelRequirement[]> = {
  kingdom_key: [
    { level: 2, itemCost: 1, materials: { bright_shard: 1 } },
    { level: 3, itemCost: 1, materials: { bright_shard: 2, dark_shard: 1 } },
    { level: 4, itemCost: 2, materials: { bright_shard: 2, dark_shard: 2 } },
    {
      level: 5,
      itemCost: 2,
      materials: { bright_shard: 3, dark_shard: 2, mythril_fragment: 1 }
    }
  ],
  mages_staff: [
    { level: 2, itemCost: 1, materials: { bright_shard: 1 } },
    {
      level: 3,
      itemCost: 1,
      materials: { bright_shard: 1, dark_shard: 1, mythril_fragment: 1 }
    },
    {
      level: 4,
      itemCost: 2,
      materials: { bright_shard: 2, dark_shard: 2, mythril_fragment: 1 }
    },
    {
      level: 5,
      itemCost: 2,
      materials: { bright_shard: 2, dark_shard: 2, mythril_fragment: 2 }
    }
  ],
  knights_shield: [
    { level: 2, itemCost: 1, materials: { dark_shard: 1 } },
    {
      level: 3,
      itemCost: 1,
      materials: { dark_shard: 2, mythril_fragment: 1 }
    },
    {
      level: 4,
      itemCost: 2,
      materials: { dark_shard: 3, mythril_fragment: 1 }
    },
    {
      level: 5,
      itemCost: 2,
      materials: { dark_shard: 3, mythril_fragment: 2 }
    }
  ],
  champion_belt: [
    { level: 2, itemCost: 1, materials: { mythril_fragment: 1 } },
    {
      level: 3,
      itemCost: 1,
      materials: { dark_shard: 1, mythril_fragment: 2 }
    },
    {
      level: 4,
      itemCost: 2,
      materials: { dark_shard: 1, mythril_fragment: 3 }
    },
    {
      level: 5,
      itemCost: 2,
      materials: { dark_shard: 2, mythril_fragment: 3 }
    }
  ],
  heros_crest: [
    { level: 2, itemCost: 1, materials: { bright_shard: 1 } },
    {
      level: 3,
      itemCost: 1,
      materials: { bright_shard: 2, mythril_fragment: 1 }
    },
    {
      level: 4,
      itemCost: 2,
      materials: { bright_shard: 2, mythril_fragment: 2 }
    },
    {
      level: 5,
      itemCost: 2,
      materials: { bright_shard: 3, mythril_fragment: 2 }
    }
  ],
  elven_bandana: [
    { level: 2, itemCost: 1, materials: { bright_shard: 1 } },
    {
      level: 3,
      itemCost: 1,
      materials: { bright_shard: 1, dark_shard: 1 }
    },
    {
      level: 4,
      itemCost: 2,
      materials: { bright_shard: 2, dark_shard: 1 }
    },
    {
      level: 5,
      itemCost: 2,
      materials: { bright_shard: 2, dark_shard: 2 }
    }
  ]
};

export function iterLevelRequirements(itemId: string): ItemLevelRequirement[] {
  return ITEM_LEVEL_TABLE[itemId] ?? [];
}

export function requirementForLevel(
  itemId: string,
  targetLevel: number
): ItemLevelRequirement | null {
  const requirements = ITEM_LEVEL_TABLE[itemId];
  if (!requirements) return null;
  const match = requirements.find((req) => req.level === targetLevel);
  return match ?? null;
}

export function maxLevel(itemId: string): number {
  const requirements = ITEM_LEVEL_TABLE[itemId];
  if (!requirements || requirements.length === 0) return 1;
  return requirements[requirements.length - 1].level;
}

export { ITEM_LEVEL_TABLE };
