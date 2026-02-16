export type SynthesisRecipe = {
  recipeId: string;
  name: string;
  materials: Record<string, number>;
  outputItemId: string;
  description: string;
};

const SYNTHESIS_RECIPES: Record<string, SynthesisRecipe> = {
  bandana_upgrade: {
    recipeId: "bandana_upgrade",
    name: "Warded Bandana",
    materials: { dark_shard: 2, bright_shard: 1 },
    outputItemId: "elven_bandana",
    description: "Imbue a bandana with protective light."
  },
  champion_belt: {
    recipeId: "champion_belt",
    name: "Champion Belt",
    materials: { dark_shard: 1, mythril_fragment: 2 },
    outputItemId: "champion_belt",
    description: "Forge a defensive belt from rare ore."
  }
};

export function iterRecipes(): SynthesisRecipe[] {
  return Object.values(SYNTHESIS_RECIPES);
}

export function getRecipe(recipeId: string): SynthesisRecipe {
  const recipe = SYNTHESIS_RECIPES[recipeId];
  if (!recipe) throw new Error(`Unknown recipe '${recipeId}'`);
  return recipe;
}

export { SYNTHESIS_RECIPES };
