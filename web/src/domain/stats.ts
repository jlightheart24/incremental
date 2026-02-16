export class Stats {
  maxHp: number;
  atk: number;
  defense: number;
  speed: number;
  mpMax: number;

  constructor(params: {
    maxHp: number;
    atk: number;
    defense: number;
    speed: number;
    mpMax?: number;
  }) {
    this.maxHp = toInt(params.maxHp);
    this.atk = toInt(params.atk);
    this.defense = toInt(params.defense);
    this.speed = toInt(params.speed);
    this.mpMax = toInt(params.mpMax ?? 10);
  }

  toString(): string {
    return `Stats(hp=${this.maxHp}, atk=${this.atk}, def=${this.defense}, spd=${this.speed}, mp_max=${this.mpMax})`;
  }
}

export class Health {
  max: number;
  current: number;

  constructor(params: { current: number; max: number }) {
    this.max = toInt(params.max);
    this.current = toInt(params.current);
    this.clamp();
  }

  clamp(): void {
    if (this.current < 0) this.current = 0;
    else if (this.current > this.max) this.current = this.max;
  }

  isDead(): boolean {
    return this.current <= 0;
  }

  ratio(): number {
    return this.max <= 0 ? 0.0 : this.current / this.max;
  }

  toString(): string {
    return `Health(${this.current}/${this.max})`;
  }
}

export class Mana {
  max: number;
  current: number;

  constructor(params: { current?: number; max?: number } = {}) {
    this.max = toInt(params.max ?? 10);
    this.current = toInt(params.current ?? 0);
    this.clamp();
  }

  clamp(): void {
    if (this.current < 0) this.current = 0;
    else if (this.current > this.max) this.current = this.max;
  }

  full(): boolean {
    return this.current >= this.max;
  }

  ratio(): number {
    return this.max <= 0 ? 0.0 : this.current / this.max;
  }

  toString(): string {
    return `Mana(${this.current}/${this.max})`;
  }
}

function toInt(value: number): number {
  return Math.trunc(value);
}
