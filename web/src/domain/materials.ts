export type Material = {
  name: string;
  description: string;
};

const MATERIAL_DB: Record<string, Material> = {
  dark_shard: {
    name: "Dark Shard",
    description: "A shard pulsing with shadowy energy."
  },
  bright_shard: {
    name: "Bright Shard",
    description: "A shard that glimmers with condensed light."
  },
  mythril_fragment: {
    name: "Mythril Fragment",
    description: "A sliver of mythril prized by craftsmen."
  }
};

export function getMaterial(materialId: string): Material {
  const template = MATERIAL_DB[materialId];
  if (!template) throw new Error(`Unknown material '${materialId}'`);
  return { ...template };
}

export function materialName(materialId: string): string {
  const material = MATERIAL_DB[materialId];
  if (!material) return materialId.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
  return material.name;
}

export { MATERIAL_DB };
