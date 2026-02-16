import Phaser from "phaser";
import {
  Actor,
  CombatSystem,
  EncounterPool,
  Enemy,
  DEFAULT_ENCOUNTER_POOLS,
  TickController,
  getLocation,
  loadState
} from "../domain";
import { saveState } from "../domain/savegame";
import { getSelectedActorIndex } from "../domain/ui_state";
import { materialName } from "../domain/materials";
import { getItem } from "../domain/items";
import { renderNavBar } from "./ui/navBar";

export class CombatDemoScene extends Phaser.Scene {
  private logText!: Phaser.GameObjects.Text;
  private logLines: string[] = [];
  private combat?: CombatSystem;
  private tickController?: TickController;
  private slotId: string | null = null;
  private rewardApplied = false;
  private encounterPool?: EncounterPool;
  private locationTitle?: string;
  private party?: Actor[];
  private uiAccum = 0;
  private reviveTimers = new Map<Actor, number>();
  private respawnDelay = 0;
  private enemyPortrait?: Phaser.GameObjects.Image;
  private enemyNameText?: Phaser.GameObjects.Text;
  private enemyInfoText?: Phaser.GameObjects.Text;
  private enemyDropsText?: Phaser.GameObjects.Text;
  private debugText?: Phaser.GameObjects.Text;
  private partyPortraits: Array<{ actor: Actor; image: Phaser.GameObjects.Image }> = [];
  private partyBars?: Phaser.GameObjects.Graphics;
  private enemyBar?: Phaser.GameObjects.Graphics;

  constructor() {
    super("CombatDemoScene");
  }

  init(data: { slotId?: string }): void {
    this.slotId = data.slotId ?? null;
  }

  create(): void {
    const { width, height } = this.scale;

    this.debugText = this.add
      .text(width - 20, height - 20, "", {
        fontFamily: "Arial",
        fontSize: "12px",
        color: "#9aa0a6"
      })
      .setOrigin(1, 1);

    if (!this.slotId) {
      this.appendLog("Missing save slot. Returning.");
      this.renderStatus();
      this.time.delayedCall(800, () => this.scene.start("GameScene"));
      return;
    }

    const state = loadState(this.slotId);
    if (state) {
      try {
        const location = getLocation(state.locationId);
        this.locationTitle = location.title;
        if (location.backgroundImage) {
          const key = `combat-bg:${location.locationId}`;
          if (!this.textures.exists(key)) {
            this.load.image(key, `/${location.backgroundImage}`);
            this.load.once(Phaser.Loader.Events.COMPLETE, () => this.scene.restart());
            this.load.start();
            if (this.debugText) {
              this.debugText.setText(`loading: ${key} | ${location.backgroundImage}`);
            }
            return;
          }
          const bg = this.add.image(width * 0.5, height * 0.5, key);
          const scale = Math.max(width / bg.width, height / bg.height);
          bg.setScale(scale);
          bg.setDepth(-10);
          if (this.debugText) {
            this.debugText.setText(`bg: ${key} | img: ${location.backgroundImage}`);
          }
        }
      } catch {
        // ignore missing location
      }
    }

    this.add
      .text(width * 0.5, 60, "Combat Demo", {
        fontFamily: "Arial",
        fontSize: "26px",
        color: "#ffffff"
      })
      .setOrigin(0.5, 0.5);

    renderNavBar(this, {
      current: "CombatDemoScene",
      slotId: this.slotId,
      targets: [
        { label: "Game", scene: "GameScene" },
        { label: "Combat", scene: "CombatDemoScene" },
        { label: "Inventory", scene: "InventoryScene" },
        { label: "Party", scene: "PartyScene" },
        { label: "Map", scene: "MapScene" }
      ]
    });

    this.logText = this.add
      .text(width * 0.5, height - 180, "", {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#dce3ea",
        align: "left",
        lineSpacing: 6
      })
      .setOrigin(0.5, 0);
    this.partyBars = this.add.graphics();
    this.enemyBar = this.add.graphics();

    this.add
      .text(width * 0.5, height - 60, "Combat auto-running. Esc to return.", {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#9ad2ff"
      })
      .setOrigin(0.5, 0.5);

    this.setupCombat(this.slotId);
    if (this.locationTitle) {
      this.add
        .text(width * 0.5, 90, this.locationTitle, {
          fontFamily: "Arial",
          fontSize: "16px",
          color: "#9aa0a6"
        })
        .setOrigin(0.5, 0.5);
    }
    this.renderStatus();
    this.preparePartyPortraits();

    this.input.keyboard?.on("keydown-ESC", () => this.scene.start("GameScene"));
  }

  update(_time: number, delta: number): void {
    if (!this.combat || !this.tickController) return;

    const dt = delta / 1000;
    this.updateRevives(dt);
    this.updateRespawn(dt);

    if (this.combat.enemy.health.isDead() && this.respawnDelay <= 0) {
      this.applyRewards();
      this.spawnNextEnemy();
    }

    if (this.respawnDelay > 0) {
      this.uiAccum += dt;
      if (this.uiAccum >= 0.2) {
        this.uiAccum = 0;
        this.renderStatus();
      }
      return;
    }

    this.tickController.update(dt, (tickDt) => {
      if (this.combat?.enemy.health.isDead()) {
        this.applyRewards();
        this.queueNextEnemy();
        return;
      }
      this.trackDeaths();
      this.combat?.onTick(tickDt);
    });

    this.uiAccum += dt;
    if (this.uiAccum >= 0.2) {
      this.uiAccum = 0;
      this.renderStatus();
    }
  }

  private setupCombat(slotId: string): void {
    const state = loadState(slotId);
    if (!state) {
      this.appendLog(`No save found for ${slotId}.`);
      return;
    }

    const location = getLocation(state.locationId);
    this.locationTitle = location.title;
    this.encounterPool = new EncounterPool({
      pools: DEFAULT_ENCOUNTER_POOLS,
      defaultPool: location.encounterPool
    });
    const enemy = this.encounterPool.nextEnemy();
    this.prepareEnemyPortrait(enemy);
    const actors = state.actors.map(
      (actor) =>
        new Actor(actor.name, {
          hp: actor.stats.maxHp,
          atk: actor.stats.atk,
          defense: actor.stats.defense,
          speed: actor.stats.speed,
          mpMax: actor.stats.mpMax,
          cd: actor.attackProfile.cooldownS,
          mpGain: actor.attackProfile.mpGainOnAttack,
          portraitPath: actor.portraitPath ?? null,
          level: actor.level,
          xp: actor.xp,
          spellId: actor.spellId ?? undefined
        })
    );
    this.party = actors;

    class LoggingCombat extends CombatSystem {
      private log: (line: string) => void;
      constructor(log: (line: string) => void, actors: Actor[], enemy: Enemy) {
        super({ actors, enemy });
        this.log = log;
      }

      basicAttack(attacker: Actor | Enemy, defender: Actor | Enemy): number {
        const dmg = super.basicAttack(attacker, defender);
        this.log(
          `${attacker.name} hits for ${dmg} | ${defender.name} HP ${defender.health.current}`
        );
        return dmg;
      }
    }

    this.combat = new LoggingCombat((line) => this.appendLog(line), actors, enemy);
    this.tickController = new TickController(0.2);
    this.appendLog(`Starting combat at ${location.title}...`);
    this.appendLog(`Party order: ${actors.map((actor) => actor.name).join(", ")}`);
    this.preparePartyPortraits();
  }

  private renderStatus(): void {
    if (!this.combat) return;
    const lines: string[] = [];
    lines.push("Party:");
    const selectedIndex = getSelectedActorIndex(0);
    this.combat.actors.forEach((actor) => {
      const revive = this.reviveTimers.get(actor);
      const status = actor.health.isDead()
        ? `DOWN${revive ? ` (${revive.toFixed(1)}s)` : ""}`
        : "OK";
      const marker = this.combat?.actors.indexOf(actor) === selectedIndex ? "*" : " ";
      lines.push(
        `${marker} ${actor.name} HP ${actor.health.current}/${actor.health.max} MP ${actor.mana.current}/${actor.mana.max} [${status}]`
      );
    });
    lines.push("");
    lines.push(`Enemy: ${this.combat.enemy.name} HP ${this.combat.enemy.health.current}/${this.combat.enemy.health.max}`);
    lines.push("");
    lines.push("Log:");
    lines.push(...this.logLines.slice(-10));
    this.logText.setText(lines.join("\n"));
    this.renderPartyBars();
    this.renderEnemyBar();
  }

  private appendLog(line: string): void {
    this.logLines.push(line);
  }

  private applyRewards(): void {
    if (this.rewardApplied || !this.slotId || !this.combat) return;
    const state = loadState(this.slotId);
    if (!state) return;

    const enemy = this.combat.enemy as Enemy;
    const xp = enemy.xpReward ?? 0;
    const munny = enemy.munnyReward ?? 0;

    if (xp > 0) {
      state.actors.forEach((actor) => actor.gainXp(xp));
      this.appendLog(`Party gained ${xp} XP each.`);
    }
    if (munny > 0) {
      state.inventory.addMunny(munny);
      this.appendLog(`Gained ${munny} munny.`);
    }

    const drops = enemy.drops ?? [];
    drops.forEach((drop) => {
      const chance = Number((drop as { chance?: number }).chance ?? 0);
      if (Math.random() > chance) return;
      const materialId = (drop as { materialId?: string }).materialId;
      const itemId = (drop as { itemId?: string }).itemId;
      const amount = Math.max(1, Math.trunc((drop as { amount?: number }).amount ?? 1));
      if (materialId) {
        state.inventory.addMaterial(materialId, amount);
        this.appendLog(`Found ${amount}x ${materialId}.`);
      } else if (itemId) {
        try {
          state.inventory.addItem(itemId);
          this.appendLog(`Found item ${itemId}.`);
        } catch (err) {
          this.appendLog(`Found item ${itemId}, but inventory is full.`);
        }
      }
    });

    saveState(state);
    this.rewardApplied = true;
  }

  private queueNextEnemy(): void {
    this.respawnDelay = 0;
    this.updateRespawn(0);
  }

  private spawnNextEnemy(): void {
    if (!this.combat || !this.encounterPool) return;
    const nextEnemy = this.encounterPool.nextEnemy();
    this.combat.enemy = nextEnemy;
    this.rewardApplied = false;
    const location = this.locationTitle ?? "Unknown";
    this.appendLog(`A new foe appears at ${location}!`);
    this.prepareEnemyPortrait(nextEnemy);
    this.renderStatus();
  }

  private trackDeaths(): void {
    if (!this.combat) return;
    this.combat.actors.forEach((actor) => {
      if (!actor.health.isDead()) return;
      if (this.reviveTimers.has(actor)) return;
      this.reviveTimers.set(actor, 10);
      this.appendLog(`${actor.name} is down! Revive in 10s.`);
    });
  }

  private updateRevives(dt: number): void {
    if (!this.combat) return;
    this.reviveTimers.forEach((timeLeft, actor) => {
      const next = timeLeft - dt;
      if (next <= 0) {
        actor.health.current = actor.health.max;
        actor.health.clamp();
        actor.mana.current = 0;
        actor.mana.clamp();
        actor.attackState.reset();
        this.reviveTimers.delete(actor);
        this.appendLog(`${actor.name} revived.`);
      } else {
        this.reviveTimers.set(actor, next);
      }
    });
  }

  private updateRespawn(dt: number): void {
    if (this.respawnDelay <= 0) return;
    this.respawnDelay -= dt;
    if (this.respawnDelay <= 0) {
      this.respawnDelay = 0;
      this.spawnNextEnemy();
    }
  }

  private prepareEnemyPortrait(enemy: Enemy): void {
    const { width } = this.scale;
    if (!enemy.portraitPath) {
      if (this.enemyPortrait) {
        this.enemyPortrait.destroy();
        this.enemyPortrait = undefined;
      }
      if (this.enemyNameText) {
        this.enemyNameText.destroy();
        this.enemyNameText = undefined;
      }
      if (this.enemyInfoText) {
        this.enemyInfoText.destroy();
        this.enemyInfoText = undefined;
      }
      if (this.enemyDropsText) {
        this.enemyDropsText.destroy();
        this.enemyDropsText = undefined;
      }
      this.renderEnemyBar();
      return;
    }
    const key = `enemy:${enemy.portraitPath}`;
    if (!this.textures.exists(key)) {
      this.load.image(key, `/${enemy.portraitPath}`);
      this.load.once(Phaser.Loader.Events.COMPLETE, () => this.prepareEnemyPortrait(enemy));
      this.load.start();
      return;
    }
    if (this.enemyPortrait) {
      this.enemyPortrait.destroy();
    }
    this.enemyPortrait = this.add.image(width - 160, 140, key);
    const maxHeight = 140;
    const scale = maxHeight / this.enemyPortrait.height;
    this.enemyPortrait.setScale(scale);
    if (this.enemyNameText) {
      this.enemyNameText.destroy();
    }
    this.enemyNameText = this.add
      .text(this.enemyPortrait.x, this.enemyPortrait.y - this.enemyPortrait.displayHeight / 2 - 10, enemy.name, {
        fontFamily: "Arial",
        fontSize: "14px",
        color: "#ffffff"
      })
      .setOrigin(0.5, 1);
    if (this.enemyInfoText) {
      this.enemyInfoText.destroy();
    }
    const level = (enemy as { level?: number }).level ?? 1;
    const xp = enemy.xpReward ?? 0;
    const munny = enemy.munnyReward ?? 0;
    this.enemyInfoText = this.add
      .text(this.enemyPortrait.x, this.enemyPortrait.y - this.enemyPortrait.displayHeight / 2 + 8, `Lv${level} | XP ${xp} | Munny ${munny}`, {
        fontFamily: "Arial",
        fontSize: "12px",
        color: "#cbd5e1"
      })
      .setOrigin(0.5, 0);
    if (this.enemyDropsText) {
      this.enemyDropsText.destroy();
    }
    const drops = enemy.drops ?? [];
    const dropLabels = drops
      .map((drop) => {
        const itemId = (drop as { itemId?: string }).itemId;
        const materialId = (drop as { materialId?: string }).materialId;
        const chance = Math.round(Number((drop as { chance?: number }).chance ?? 0) * 100);
        if (itemId) {
          try {
            const item = getItem(itemId);
            return `${item.name} (${chance}%)`;
          } catch {
            return `${itemId} (${chance}%)`;
          }
        }
        if (materialId) {
          return `${materialName(materialId)} (${chance}%)`;
        }
        return null;
      })
      .filter(Boolean);
    this.enemyDropsText = this.add
      .text(
        this.enemyPortrait.x,
        this.enemyPortrait.y - this.enemyPortrait.displayHeight / 2 + 26,
        dropLabels.length ? `Drops: ${dropLabels.join(", ")}` : "Drops: (none)",
        {
          fontFamily: "Arial",
          fontSize: "12px",
          color: "#9aa0a6",
          align: "center",
          wordWrap: { width: 260 }
        }
      )
      .setOrigin(0.5, 0);
    this.renderEnemyBar();
  }

  private preparePartyPortraits(): void {
    if (!this.combat) return;
    const { width, height } = this.scale;
    this.partyPortraits.forEach((portrait) => portrait.image.destroy());
    this.partyPortraits = [];

    const portraits = this.combat.actors
      .map((actor) => ({ actor, path: actor.portraitPath }))
      .filter((entry): entry is { actor: Actor; path: string } => Boolean(entry.path));
    if (portraits.length === 0) return;

    const missing = portraits.filter((entry) => !this.textures.exists(`portrait:${entry.path}`));
    if (missing.length > 0) {
      missing.forEach((entry) => this.load.image(`portrait:${entry.path}`, `/${entry.path}`));
      this.load.once(Phaser.Loader.Events.COMPLETE, () => this.preparePartyPortraits());
      this.load.start();
      return;
    }

    const startX = 100;
    portraits.forEach((entry, index) => {
      const key = `portrait:${entry.path}`;
      const img = this.add.image(startX, 180 + index * 180, key);
      const maxHeight = 120;
      const scale = maxHeight / img.height;
      img.setScale(scale);
      this.partyPortraits.push({ actor: entry.actor, image: img });
    });
    this.renderPartyBars();
  }

  private renderPartyBars(): void {
    if (!this.partyBars) return;
    this.partyBars.clear();
    this.partyBars.setDepth(5);
    const barWidth = 120;
    const barHeight = 8;
    const mpHeight = 6;

    this.partyPortraits.forEach(({ actor, image }) => {
      const x = image.x - barWidth / 2;
      const y = image.y + image.displayHeight / 2 + 8;
      const hpRatio = actor.health.ratio();
      const mpRatio = actor.mana.ratio();

      // HP background
      this.partyBars.fillStyle(0x1f2937, 1);
      this.partyBars.fillRect(x, y, barWidth, barHeight);
      // HP fill
      this.partyBars.fillStyle(0x22c55e, 1);
      this.partyBars.fillRect(x, y, barWidth * hpRatio, barHeight);

      // MP background
      this.partyBars.fillStyle(0x1f2937, 1);
      this.partyBars.fillRect(x, y + barHeight + 4, barWidth, mpHeight);
      // MP fill
      this.partyBars.fillStyle(0x38bdf8, 1);
      this.partyBars.fillRect(x, y + barHeight + 4, barWidth * mpRatio, mpHeight);
    });
  }

  private renderEnemyBar(): void {
    if (!this.enemyBar) return;
    this.enemyBar.clear();
    this.enemyBar.setDepth(5);
    if (!this.combat?.enemy || !this.enemyPortrait) return;

    const barWidth = 160;
    const barHeight = 10;
    const hpRatio = this.combat.enemy.health.ratio();
    const x = this.enemyPortrait.x - barWidth / 2;
    const y = this.enemyPortrait.y + this.enemyPortrait.displayHeight / 2 + 6;

    this.enemyBar.fillStyle(0x1f2937, 1);
    this.enemyBar.fillRect(x, y, barWidth, barHeight);
    this.enemyBar.fillStyle(0xef4444, 1);
    this.enemyBar.fillRect(x, y, barWidth * hpRatio, barHeight);
  }

  // Auto-run now driven by Phaser's update loop.
}
