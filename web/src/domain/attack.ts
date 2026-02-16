export class AttackProfile {
  cooldownS: number;
  mpGainOnAttack: number;

  constructor(params: { cooldownS: number; mpGainOnAttack?: number }) {
    this.cooldownS = Number(params.cooldownS);
    this.mpGainOnAttack = Math.trunc(params.mpGainOnAttack ?? 1);
  }

  toString(): string {
    return `AttackProfile(cd=${this.cooldownS}s, mp+=${this.mpGainOnAttack})`;
  }
}

export class AttackState {
  timeSinceAttackS: number;

  constructor() {
    this.timeSinceAttackS = 0.0;
  }

  tick(dt: number): void {
    this.timeSinceAttackS += Number(dt);
  }

  ready(cooldownS: number): boolean {
    return this.timeSinceAttackS >= Number(cooldownS);
  }

  reset(): void {
    this.timeSinceAttackS = 0.0;
  }

  toString(): string {
    return `AttackState(t=${this.timeSinceAttackS.toFixed(2)}s)`;
  }
}
