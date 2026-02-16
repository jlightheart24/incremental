import { describe, expect, test } from "vitest";
import { CombatSystem, TickController } from "../combat";
import { Actor, Enemy } from "../entities";

class SpyCombat extends CombatSystem {
  attacks: Array<{ attacker: Actor | Enemy; defender: Actor | Enemy }> = [];

  basicAttack(attacker: Actor | Enemy, defender: Actor | Enemy): number {
    this.attacks.push({ attacker, defender });
    return 0;
  }
}

describe("TickController", () => {
  test("calls on fixed threshold", () => {
    const tc = new TickController(0.2);
    const calls: number[] = [];
    const cb = (dt: number) => calls.push(dt);

    tc.update(0.05, cb);
    expect(calls).toEqual([]);

    tc.update(0.1, cb);
    expect(calls).toEqual([]);

    tc.update(0.05, cb);
    expect(calls).toEqual([0.2]);

    tc.update(0.4, cb);
    expect(calls).toEqual([0.2, 0.2, 0.2]);
  });
});

describe("CombatSystem.onTick", () => {
  test("actor attacks once when cooldown reached", () => {
    const a = new Actor("A", { cd: 0.2 });
    const e = new Enemy({});
    const cs = new SpyCombat({ actors: [a], enemy: e });

    cs.onTick(0.1);
    expect(cs.attacks.length).toBe(0);

    cs.onTick(0.1);
    expect(cs.attacks.length).toBe(1);
    expect(cs.attacks[0].attacker).toBe(a);
    expect(cs.attacks[0].defender).toBe(e);
  });

  test("skips dead actor and stops if enemy dead", () => {
    const a1 = new Actor("A1", { cd: 0.1 });
    const a2 = new Actor("A2", { cd: 0.1 });
    const e = new Enemy({});
    const cs = new SpyCombat({ actors: [a1, a2], enemy: e });

    a1.health.current = 0;
    a1.health.clamp();

    cs.onTick(0.1);
    expect(cs.attacks.length).toBe(1);
    expect(cs.attacks[0].attacker).toBe(a2);

    e.health.current = 0;
    e.health.clamp();

    cs.onTick(1.0);
    expect(cs.attacks.length).toBe(1);
  });
});

describe("CombatSystem.basicAttack", () => {
  test("applies damage, grants mp, and resets", () => {
    const a = new Actor("A", { hp: 10, atk: 5, defense: 0, mpMax: 3, cd: 0.2, mpGain: 2 });
    const e = new Enemy({ hp: 9, defense: 3 });

    class CS extends CombatSystem {}
    const cs = new CS({ actors: [a], enemy: e });

    a.attackState.tick(0.5);
    expect(a.attackState.timeSinceAttackS).toBeGreaterThan(0);

    const dmg = cs.basicAttack(a, e);

    const expected = Math.max(1, a.stats.atk - e.stats.defense);
    expect(dmg).toBe(expected);
    expect(e.health.current).toBe(9 - expected);

    const expectedMp = Math.min(a.mana.max, 0 + a.attackProfile.mpGainOnAttack);
    expect(a.mana.current).toBe(expectedMp);

    expect(a.attackState.timeSinceAttackS).toBe(0.0);
  });
});
