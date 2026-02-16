import { describe, expect, test } from "vitest";
import { Actor, Enemy } from "../entities";



describe("Actor/Enemy wiring", () => {
  test("defaults and spell logic", () => {
    const a = new Actor("TEST", { hp: 7, atk: 4, defense: 1, mpMax: 3, cd: 0.2, mpGain: 2 });
    const e = new Enemy({ hp: 9, defense: 3 });

    expect(a.stats.atk).toBe(4);
    expect(a.health.current).toBe(7);
    expect(a.mana.max).toBe(3);
    expect(a.attackProfile.cooldownS).toBe(0.2);
    expect(a.portraitPath).toBe(null);
    expect(a.currentSpell).toBe(null);
    expect(a.level).toBe(1);
    expect(a.xp).toBe(0);
    expect(a.xpToLevel).toBe(100);

    a.setSpell("fire");
    expect(a.currentSpell?.name).toBe("Fire");
    expect(a.magicDamage).toBe(a.currentSpell?.damage);
    expect(a.mana.max).toBe(a.currentSpell?.mpMax);

    expect(e.stats.defense).toBe(3);
    expect(e.health.current).toBe(9);
    expect(e.portraitPath).toBe(null);
  });
});
