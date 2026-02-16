import Phaser from "phaser";
import { getLocation } from "../domain/locations";
import { renderNavBar } from "./ui/navBar";
import { loadState, saveState } from "../domain/savegame";

export class GameScene extends Phaser.Scene {
  private slotId: string | null = null;

  constructor() {
    super("GameScene");
  }

  init(data: { slotId?: string }): void {
    this.slotId = data.slotId ?? null;
  }

  create(): void {
    const { width, height } = this.scale;
    if (!this.slotId) {
      this.scene.start("LoadSaveScene");
      return;
    }

    const state = loadState(this.slotId);
    const title = state ? `Loaded ${this.slotId}` : `Missing ${this.slotId}`;

    let locationDef = null as ReturnType<typeof getLocation> | null;
    if (state) {
      try {
        locationDef = getLocation(state.locationId);
      } catch {
        locationDef = null;
      }
    }

    if (state) {
      const portraitPaths = state.actors
        .map((actor) => actor.portraitPath)
        .filter((path): path is string => Boolean(path));
      const missingPortraits = portraitPaths.filter((path) => !this.textures.exists(`portrait:${path}`));
      if (missingPortraits.length > 0) {
        missingPortraits.forEach((path) => {
          this.load.image(`portrait:${path}`, `/${path}`);
        });
        this.load.once(Phaser.Loader.Events.COMPLETE, () => this.scene.restart());
        this.load.start();
        return;
      }
    }

    if (locationDef?.backgroundImage) {
      const key = `bg:${locationDef.locationId}`;
      if (!this.textures.exists(key)) {
        this.load.image(key, `/${locationDef.backgroundImage}`);
        this.load.once(Phaser.Loader.Events.COMPLETE, () => this.scene.restart());
        this.load.start();
        return;
      }
      const bg = this.add.image(width * 0.5, height * 0.5, key);
      const scale = Math.max(width / bg.width, height / bg.height);
      bg.setScale(scale);
      bg.setDepth(-10);
    }

    renderNavBar(this, {
      current: "GameScene",
      slotId: this.slotId,
      targets: [
        { label: "Game", scene: "GameScene" },
        { label: "Combat", scene: "CombatDemoScene" },
        { label: "Inventory", scene: "InventoryScene" },
        { label: "Party", scene: "PartyScene" },
        { label: "Map", scene: "MapScene" }
      ]
    });

    this.add
      .text(width * 0.5, 100, title, {
        fontFamily: "Arial",
        fontSize: "26px",
        color: "#ffffff"
      })
      .setOrigin(0.5, 0.5);

    if (state) {
      const party = state.actors.map((actor) => actor.name).join(", ");
      this.add
        .text(width * 0.5, 160, `Party: ${party}`, {
          fontFamily: "Arial",
          fontSize: "18px",
          color: "#cbd5e1"
        })
        .setOrigin(0.5, 0.5);

      this.add
        .text(width * 0.5, 210, `Location: ${state.locationId}`, {
          fontFamily: "Arial",
          fontSize: "18px",
          color: "#cbd5e1"
        })
        .setOrigin(0.5, 0.5);

      if (locationDef) {
        this.add
          .text(width * 0.5, 240, `${locationDef.title} - ${locationDef.subtitle}`, {
            fontFamily: "Arial",
            fontSize: "16px",
            color: "#9aa0a6"
          })
          .setOrigin(0.5, 0.5);
      }

      const portraits = state.actors
        .map((actor) => ({
          name: actor.name,
          path: actor.portraitPath
        }))
        .filter((entry): entry is { name: string; path: string } => Boolean(entry.path));
      if (portraits.length > 0) {
        const startX = width * 0.5 - (portraits.length - 1) * 90;
        portraits.forEach((entry, index) => {
          const key = `portrait:${entry.path}`;
          const img = this.add.image(startX + index * 180, height - 170, key);
          const maxHeight = 160;
          const scale = maxHeight / img.height;
          img.setScale(scale);
          this.add
            .text(img.x, img.y + maxHeight * 0.65, entry.name, {
              fontFamily: "Arial",
              fontSize: "14px",
              color: "#ffffff"
            })
            .setOrigin(0.5, 0.5);
        });
      }

      const leftLines: string[] = [];
      leftLines.push(`Munny: ${state.inventory.munny}`);
      const materialLines = Object.entries(state.inventory.materials).map(
        ([id, qty]) => `${id}: ${qty}`
      );
      leftLines.push("Materials:");
      leftLines.push(...(materialLines.length ? materialLines : ["(none)"]));
      const itemLines = state.inventory.itemList.length
        ? state.inventory.itemList.map((id) => `- ${id}`)
        : ["(none)"];
      leftLines.push("Items:");
      leftLines.push(...itemLines);

      const rightLines: string[] = [];
      rightLines.push("Party Stats:");
      state.actors.forEach((actor) => {
        rightLines.push(
          `${actor.name} | HP ${actor.health.current}/${actor.health.max} | MP ${actor.mana.current}/${actor.mana.max}`
        );
        rightLines.push(
          `Atk ${actor.stats.atk} Def ${actor.stats.defense} Spd ${actor.stats.speed} CD ${actor.attackProfile.cooldownS}`
        );
        const equipmentEntries = actor.equipment
          ? Object.entries(actor.equipment).map(
              ([slot, entry]) => `${slot}: ${(entry as { itemId: string }).itemId}`
            )
          : [];
        rightLines.push(
          equipmentEntries.length
            ? `Equip ${equipmentEntries.join(", ")}`
            : "Equip (none)"
        );
      });

      this.add
        .text(80, 270, leftLines.join("\n"), {
          fontFamily: "Arial",
          fontSize: "16px",
          color: "#dce3ea",
          align: "left"
        })
        .setOrigin(0, 0);

      this.add
        .text(width * 0.5, 270, rightLines.join("\n"), {
          fontFamily: "Arial",
          fontSize: "16px",
          color: "#dce3ea",
          align: "left"
        })
        .setOrigin(0, 0);
    }

    this.add
      .text(
        width * 0.5,
        height - 100,
        "Press S to quick-save, C for combat demo, I for inventory, P for party, M for map, Esc to return.",
        {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#9ad2ff"
      }
      )
      .setOrigin(0.5, 0.5);

    this.input.keyboard?.on("keydown-ESC", () => this.scene.start("LoadSaveScene"));
    this.input.keyboard?.on("keydown-C", () =>
      this.scene.start("CombatDemoScene", { slotId: this.slotId })
    );
    this.input.keyboard?.on("keydown-I", () =>
      this.scene.start("InventoryScene", { slotId: this.slotId })
    );
    this.input.keyboard?.on("keydown-P", () =>
      this.scene.start("PartyScene", { slotId: this.slotId })
    );
    this.input.keyboard?.on("keydown-M", () =>
      this.scene.start("MapScene", { slotId: this.slotId })
    );
    this.input.keyboard?.on("keydown-S", () => {
      if (!this.slotId) return;
      const current = loadState(this.slotId);
      if (!current) return;
      saveState(current);
      this.flashMessage("Saved.");
    });
  }

  private flashMessage(message: string): void {
    const { width, height } = this.scale;
    const label = this.add
      .text(width * 0.5, height - 140, message, {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#7ee787"
      })
      .setOrigin(0.5, 0.5);

    this.tweens.add({
      targets: label,
      alpha: 0,
      duration: 800,
      delay: 400,
      onComplete: () => label.destroy()
    });
  }
}
