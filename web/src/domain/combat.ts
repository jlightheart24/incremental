import { calcDamage } from "./damage";
import { Character } from "./entities";

export class TickController {
  tickLengthS: number;
  private accum: number;

  constructor(tickLengthS = 0.2) {
    this.tickLengthS = Number(tickLengthS);
    this.accum = 0.0;
  }

  update(dt: number, onTick: (dt: number) => void): void {
    this.accum += Number(dt);
    while (this.accum >= this.tickLengthS) {
      onTick(this.tickLengthS);
      this.accum -= this.tickLengthS;
    }
  }

  toString(): string {
    return `TickController(dt=${this.tickLengthS}s, accum=${this.accum.toFixed(3)})`;
  }
}

export class CombatSystem {
  actors: Character[];
  enemy: Character;
  private selectActorTarget: (actor: Character) => Character | null;
  private selectEnemyTarget: (enemy: Character) => Character | null;

  constructor(params: {
    actors: Character[];
    enemy: Character;
    selectActorTarget?: (actor: Character) => Character | null;
    selectEnemyTarget?: (enemy: Character) => Character | null;
  }) {
    this.actors = params.actors;
    this.enemy = params.enemy;
    this.selectActorTarget = params.selectActorTarget ?? ((_) => this.enemy);
    this.selectEnemyTarget =
      params.selectEnemyTarget ?? ((_) => this.actors.find((actor) => !actor.health.isDead()) ?? null);
  }

  onTick(dt: number): void {
    this.actors.forEach((actor) => {
      if (actor.health.isDead()) return;
      actor.attackState.tick(dt);
      if (!actor.attackState.ready(actor.attackProfile.cooldownS)) return;
      const target = this.selectActorTarget(actor);
      if (!target || target.health.isDead()) return;
      this.basicAttack(actor, target);
    });

    if (this.enemy.health.isDead()) return;

    this.enemy.attackState.tick(dt);
    if (!this.enemy.attackState.ready(this.enemy.attackProfile.cooldownS)) return;
    const target = this.selectEnemyTarget(this.enemy);
    if (!target || target.health.isDead()) return;
    this.basicAttack(this.enemy, target);
  }

  basicAttack(attacker: Character, defender: Character): number {
    let damage = calcDamage(attacker.stats.atk, defender.stats.defense);
    const mana = (attacker as { mana?: { full(): boolean; current: number; clamp(): void; max: number } }).mana;
    if (mana && mana.full()) {
      damage += (attacker as { magicDamage?: number }).magicDamage ?? 0;
      mana.current = 0;
    }
    defender.health.current -= damage;
    defender.health.clamp();
    if (mana) {
      mana.current += attacker.attackProfile.mpGainOnAttack;
      mana.clamp();
    }
    attacker.attackState.reset();
    return damage;
  }

  toString(): string {
    const enemyName = (this.enemy as { name?: string }).name ?? "Enemy";
    return `CombatSystem(actors=${this.actors.length}, enemy=${enemyName})`;
  }
}
