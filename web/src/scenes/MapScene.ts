import Phaser from "phaser";
import { getLocation, iterLocations } from "../domain/locations";
import { loadState, saveState } from "../domain/savegame";
import { renderNavBar } from "./ui/navBar";

export class MapScene extends Phaser.Scene {
  private slotId: string | null = null;
  private selectedIndex = 0;
  private messageText?: Phaser.GameObjects.Text;
  private selectionText?: Phaser.GameObjects.Text;
  private locationsCache: ReturnType<typeof iterLocations> = [];
  private locationLineTexts: Phaser.GameObjects.Text[] = [];
  private bgImage?: Phaser.GameObjects.Image;
  private bgKey?: string;
  private debugText?: Phaser.GameObjects.Text;
  private pendingBgKey?: string;
  private isShuttingDown = false;

  constructor() {
    super("MapScene");
  }

  init(data: { slotId?: string; selectedIndex?: number }): void {
    this.slotId = data.slotId ?? null;
    if (typeof data.selectedIndex === "number") {
      this.selectedIndex = data.selectedIndex;
    }
  }

  create(): void {
    this.isShuttingDown = false;
    const { width, height } = this.scale;
    this.cameras.main.setBackgroundColor("#0b0f16");
    this.add
      .rectangle(width * 0.5, height * 0.5, width, height, 0x0b0f16, 1)
      .setDepth(-20);
    // Temporary visual sanity layer.
    this.add
      .rectangle(width * 0.5, height * 0.5, width, height, 0x1e293b, 0.25)
      .setDepth(0);

    // Always-visible marker to confirm scene rendered.
    const marker = this.add
      .text(20, height - 40, "MapScene active", {
        fontFamily: "Arial",
        fontSize: "12px",
        color: "#9aa0a6"
      })
      .setOrigin(0, 1)
      .setDepth(50);
    if (!this.slotId) {
      marker.setText("MapScene active (no slotId)");
      return;
    }

    const state = loadState(this.slotId);
    if (!state) {
      marker.setText("MapScene active (missing state)");
      return;
    }

    try {
      const currentLocation = getLocation(state.locationId);
      this.setBackground(currentLocation);
    } catch {
      marker.setText(`MapScene active (bad location: ${state.locationId})`);
    }

    const locations = Array.from(iterLocations());
    this.locationsCache = locations;
    if (this.selectedIndex >= locations.length) {
      this.selectedIndex = 0;
    }

    this.add
      .text(width * 0.5, 60, "Map", {
        fontFamily: "Arial",
        fontSize: "26px",
        color: "#ffffff"
      })
      .setOrigin(0.5, 0.5)
      .setDepth(5);

    renderNavBar(this, {
      current: "MapScene",
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
      .text(width * 0.5, height - 60, "Enter to travel, Esc to return", {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#9ad2ff"
      })
      .setOrigin(0.5, 0.5)
      .setDepth(5);

    this.messageText = this.add
      .text(width * 0.5, height - 100, "", {
        fontFamily: "Arial",
        fontSize: "14px",
        color: "#7ee787"
      })
      .setOrigin(0.5, 0.5);
    this.messageText.setDepth(5);

    this.selectionText = this.add
      .text(width * 0.5, 100, "", {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#cbd5e1"
      })
      .setOrigin(0.5, 0.5);
    this.selectionText.setDepth(5);

    this.debugText = this.add
      .text(20, height - 20, "", {
        fontFamily: "Arial",
        fontSize: "12px",
        color: "#9aa0a6"
      })
      .setOrigin(0, 1);
    this.debugText.setDepth(10);

    this.load.on("loaderror", this.onLoadError, this);
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      this.isShuttingDown = true;
      this.pendingBgKey = undefined;
      this.load.off("loaderror", this.onLoadError, this);
    });

    this.locationLineTexts = [];
    this.add
      .text(80, 120, "Locations:", {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#dce3ea"
      })
      .setOrigin(0, 0)
      .setDepth(5);

    locations.forEach((location, index) => {
      const current = location.locationId === state.locationId ? " (current)" : "";
      const line = this.add
        .text(100, 150 + index * 28, `${location.title} - ${location.subtitle}${current}`, {
          fontFamily: "Arial",
          fontSize: "16px",
          color: "#dce3ea"
        })
        .setOrigin(0, 0)
        .setInteractive({ useHandCursor: true });
      line.setDepth(5);
      line.on("pointerover", () => {
        this.selectedIndex = index;
        this.updateSelectionText();
      });
      line.on("pointerup", () => {
        this.selectedIndex = index;
        const selected = locations[index];
        this.applyTravel(state, selected);
      });
      this.locationLineTexts.push(line);
    });

    this.updateSelectionText();

    this.input.keyboard?.on("keydown-ESC", () => this.scene.start("GameScene", { slotId: this.slotId }));

    this.input.keyboard?.on("keydown", (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (!this.slotId) return;

      if (key === "q" || key === "arrowup") {
        this.selectedIndex = (this.selectedIndex - 1 + locations.length) % locations.length;
        this.updateSelectionText();
        return;
      }
      if (key === "e" || key === "arrowdown") {
        this.selectedIndex = (this.selectedIndex + 1) % locations.length;
        this.updateSelectionText();
        return;
      }
      if (key === "enter") {
        const selected = locations[this.selectedIndex];
        this.applyTravel(state, selected);
      }
    });
  }

  private updateSelectionText(): void {
    if (!this.selectionText || this.locationsCache.length === 0) return;
    const location = this.locationsCache[this.selectedIndex];
    this.selectionText.setText(`Selected: ${location.title} - ${location.subtitle}`);
    this.locationLineTexts.forEach((text, index) => {
      text.setStyle({
        color: index === this.selectedIndex ? "#ffffff" : "#dce3ea"
      });
    });
  }

  private setBackground(location: ReturnType<typeof getLocation>): void {
    if (this.isShuttingDown) return;
    if (!location.backgroundImage) return;
    const key = `map-bg:${location.locationId}`;
    if (!this.textures.exists(key)) {
      if (this.pendingBgKey !== key && !this.load.isLoading()) {
        this.pendingBgKey = key;
        this.load.image(key, `/${location.backgroundImage}`);
        this.load.once(Phaser.Loader.Events.COMPLETE, () => {
          this.pendingBgKey = undefined;
          if (this.isShuttingDown || !this.sys.isActive()) return;
          this.setBackground(location);
        });
        this.load.start();
      }
      if (this.debugText) {
        this.debugText.setText(`loading: ${key} | ${location.backgroundImage}`);
      }
      return;
    }
    const { width, height } = this.scale;
    if (!this.bgImage) {
      this.bgImage = this.add.image(width * 0.5, height * 0.5, key);
      this.bgImage.setDepth(-10);
    } else if (this.bgKey !== key) {
      this.bgImage.setTexture(key);
    }
    this.bgKey = key;
    this.bgImage.setVisible(true);
    this.bgImage.setAlpha(1);
    const scale = Math.max(width / this.bgImage.width, height / this.bgImage.height);
    this.bgImage.setScale(scale);
    if (this.debugText) {
      this.debugText.setText(`bg: ${key} | img: ${location.backgroundImage} | exists: true`);
    }
  }

  private onLoadError(file: Phaser.Loader.File): void {
    if (!this.debugText || this.isShuttingDown) return;
    this.debugText.setText(`loaderror: ${file.key} | ${file.src}`);
  }

  private setMessage(message: string): void {
    if (!this.messageText) return;
    this.messageText.setText(message);
  }

  private applyTravel(state: ReturnType<typeof loadState>, selected: ReturnType<typeof getLocation>): void {
    if (!state) return;
    state.locationId = selected.locationId;
    saveState(state);
    this.setMessage(`Traveled to ${selected.title} - ${selected.subtitle}.`);
    this.setBackground(selected);
    this.updateSelectionText();
  }
}
