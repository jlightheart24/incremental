import Phaser from "phaser";
import { loadState, saveState } from "../domain/savegame";
import { getSelectedActorIndex, setSelectedActorIndex } from "../domain/ui_state";
import { renderNavBar } from "./ui/navBar";

export class PartyScene extends Phaser.Scene {
  private slotId: string | null = null;
  private selectedIndex = 0;
  private messageText?: Phaser.GameObjects.Text;

  constructor() {
    super("PartyScene");
  }

  init(data: { slotId?: string; selectedIndex?: number }): void {
    this.slotId = data.slotId ?? null;
    if (typeof data.selectedIndex === "number") {
      this.selectedIndex = data.selectedIndex;
      setSelectedActorIndex(this.selectedIndex);
    } else {
      this.selectedIndex = getSelectedActorIndex(0);
    }
  }

  create(): void {
    const { width, height } = this.scale;
    if (!this.slotId) {
      this.scene.start("GameScene");
      return;
    }

    const state = loadState(this.slotId);
    if (!state) {
      this.scene.start("GameScene");
      return;
    }

    if (this.selectedIndex >= state.actors.length) {
      this.selectedIndex = 0;
      setSelectedActorIndex(this.selectedIndex);
    }

    this.add
      .text(width * 0.5, 60, "Party", {
        fontFamily: "Arial",
        fontSize: "26px",
        color: "#ffffff"
      })
      .setOrigin(0.5, 0.5);

    renderNavBar(this, {
      current: "PartyScene",
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
      .text(width * 0.5, height - 60, "Esc to return", {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#9ad2ff"
      })
      .setOrigin(0.5, 0.5);

    this.messageText = this.add
      .text(width * 0.5, height - 100, "", {
        fontFamily: "Arial",
        fontSize: "14px",
        color: "#7ee787"
      })
      .setOrigin(0.5, 0.5);

    const lines: string[] = [];
    lines.push("Party Order:");
    state.actors.forEach((actor, index) => {
      const marker = index === this.selectedIndex ? "*" : " ";
      lines.push(`${marker} ${index + 1}. ${actor.name}`);
    });

    lines.push("");
    lines.push("Stats:");
    state.actors.forEach((actor) => {
      lines.push(
        `${actor.name} | Lv${actor.level} | HP ${actor.health.current}/${actor.health.max} | MP ${actor.mana.current}/${actor.mana.max}`
      );
      lines.push(`Atk ${actor.stats.atk} Def ${actor.stats.defense} Spd ${actor.stats.speed}`);
    });

    lines.push("");
    lines.push("Controls:");
    lines.push("Q/E: Select party member");
    lines.push("Z: Move selected up");
    lines.push("X: Move selected down");

    this.add
      .text(80, 120, lines.join("\n"), {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#dce3ea",
        align: "left",
        lineSpacing: 6
      })
      .setOrigin(0, 0);

    this.input.keyboard?.on("keydown-ESC", () => this.scene.start("GameScene", { slotId: this.slotId }));

    this.input.keyboard?.on("keydown", (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (!this.slotId) return;

      if (key === "q") {
        this.selectedIndex = (this.selectedIndex - 1 + state.actors.length) % state.actors.length;
        setSelectedActorIndex(this.selectedIndex);
        this.scene.start("PartyScene", { slotId: this.slotId, selectedIndex: this.selectedIndex });
        return;
      }
      if (key === "e") {
        this.selectedIndex = (this.selectedIndex + 1) % state.actors.length;
        setSelectedActorIndex(this.selectedIndex);
        this.scene.start("PartyScene", { slotId: this.slotId, selectedIndex: this.selectedIndex });
        return;
      }
      if (key === "z") {
        if (this.selectedIndex <= 0) return;
        const swapIndex = this.selectedIndex - 1;
        [state.actors[this.selectedIndex], state.actors[swapIndex]] = [
          state.actors[swapIndex],
          state.actors[this.selectedIndex]
        ];
        this.selectedIndex = swapIndex;
        saveState(state);
        this.setMessage("Moved up.");
        this.scene.start("PartyScene", { slotId: this.slotId, selectedIndex: this.selectedIndex });
        return;
      }
      if (key === "x") {
        if (this.selectedIndex >= state.actors.length - 1) return;
        const swapIndex = this.selectedIndex + 1;
        [state.actors[this.selectedIndex], state.actors[swapIndex]] = [
          state.actors[swapIndex],
          state.actors[this.selectedIndex]
        ];
        this.selectedIndex = swapIndex;
        saveState(state);
        this.setMessage("Moved down.");
        this.scene.start("PartyScene", { slotId: this.slotId, selectedIndex: this.selectedIndex });
      }
    });
  }

  private setMessage(message: string): void {
    if (!this.messageText) return;
    this.messageText.setText(message);
  }
}
