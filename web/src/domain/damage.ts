export function calcDamage(atk: number, defense: number): number {
  const a = Math.trunc(atk);
  const d = Math.trunc(defense);
  return Math.max(1, a - d);
}
