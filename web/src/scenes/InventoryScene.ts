import Phaser from "phaser";
import { loadState } from "../domain/savegame";
import { getSelectedActorIndex, setSelectedActorIndex } from "../domain/ui_state";
import { renderNavBar } from "./ui/navBar";

export class InventoryScene extends Phaser.Scene {
  private slotId: string | null = null;
  private messageText?: Phaser.GameObjects.Text;
  private selectedActorIndex = 0;

  constructor() {
    super("InventoryScene");
  }

  init(data: { slotId?: string; selectedActorIndex?: number }): void {
    this.slotId = data.slotId ?? null;
    if (typeof data.selectedActorIndex === "number") {
      this.selectedActorIndex = data.selectedActorIndex;
      setSelectedActorIndex(this.selectedActorIndex);
    } else {
      this.selectedActorIndex = getSelectedActorIndex(0);
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
    if (this.selectedActorIndex >= state.actors.length) {
      this.selectedActorIndex = 0;
      setSelectedActorIndex(this.selectedActorIndex);
    }

    this.add
      .text(width * 0.5, 60, "Inventory", {
        fontFamily: "Arial",
        fontSize: "26px",
        color: "#ffffff"
      })
      .setOrigin(0.5, 0.5);

    renderNavBar(this, {
      current: "InventoryScene",
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

    const leftLines: string[] = [];
    leftLines.push(`Munny: ${state.inventory.munny}`);
    leftLines.push("");
    leftLines.push("Materials:");
    const materials = Object.entries(state.inventory.materials);
    if (materials.length === 0) leftLines.push("(none)");
    materials.forEach(([id, qty]) => leftLines.push(`${id}: ${qty}`));

    this.add
      .text(80, 120, leftLines.join("\n"), {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#dce3ea",
        align: "left",
        lineSpacing: 6
      })
      .setOrigin(0, 0);

    const rightLines: string[] = [];
    rightLines.push("Items:");
    const items = state.inventory.itemList;
    if (items.length === 0) rightLines.push("(none)");
    items.forEach((itemId, index) => rightLines.push(`${index + 1}. ${itemId}`));

    rightLines.push("");
    rightLines.push("Equipped:");
    state.actors.forEach((actor, index) => {
      const marker = index === this.selectedActorIndex ? "*" : " ";
      rightLines.push(`${marker} ${actor.name}:`);
      const equipmentEntries = actor.equipment ? Object.entries(actor.equipment) : [];
      if (equipmentEntries.length === 0) {
        rightLines.push("  (none)");
        return;
      }
      equipmentEntries.forEach(([slot, entry]) => {
        const itemId = (entry as { itemId: string }).itemId;
        rightLines.push(`  ${slot}: ${itemId}`);
      });
    });

    rightLines.push("");
    rightLines.push("Controls:");
    rightLines.push("Q/E: Select actor");
    rightLines.push("1-9: Equip item to selected actor");
    rightLines.push("K: Unequip keyblade");
    rightLines.push("A: Unequip armor");
    rightLines.push("X: Unequip accessory");

    this.add
      .text(width * 0.5, 120, rightLines.join("\n"), {
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
        this.selectedActorIndex =
          (this.selectedActorIndex - 1 + state.actors.length) % state.actors.length;
        setSelectedActorIndex(this.selectedActorIndex);
        this.setMessage(`Selected: ${state.actors[this.selectedActorIndex].name}`);
        this.scene.start("InventoryScene", {
          slotId: this.slotId,
          selectedActorIndex: this.selectedActorIndex
        });
        return;
      }
      if (key === "e") {
        this.selectedActorIndex =
          (this.selectedActorIndex + 1) % state.actors.length;
        setSelectedActorIndex(this.selectedActorIndex);
        this.setMessage(`Selected: ${state.actors[this.selectedActorIndex].name}`);
        this.scene.start("InventoryScene", {
          slotId: this.slotId,
          selectedActorIndex: this.selectedActorIndex
        });
        return;
      }
      if (key >= "1" && key <= "9") {
        const index = Number(key) - 1;
        const itemId = items[index];
        if (!itemId) {
          this.setMessage("No item in that slot.", true);
          return;
        }
        try {
          const actor = state.actors[this.selectedActorIndex];
          state.inventory.equipItem(actor, itemId);
          this.setMessage(`Equipped ${itemId} on ${actor.name}.`);
          this.persistAndRefresh(state);
        } catch (err) {
          this.setMessage((err as Error).message, true);
        }
        return;
      }
      if (key === "k") {
        this.handleUnequip(state, "keyblade");
        return;
      }
      if (key === "a") {
        this.handleUnequip(state, "armor");
        return;
      }
      if (key === "x") {
        this.handleUnequip(state, "accessory");
      }
    });
  }

  private handleUnequip(state: ReturnType<typeof loadState>, slot: string): void {
    if (!state || !this.slotId) return;
    try {
      const actor = state.actors[this.selectedActorIndex];
      state.inventory.unequipSlot(actor, slot);
      this.setMessage(`Unequipped ${slot} from ${actor.name}.`);
      this.persistAndRefresh(state);
    } catch (err) {
      this.setMessage((err as Error).message, true);
    }
  }

  private persistAndRefresh(state: ReturnType<typeof loadState>): void {
    if (!state || !this.slotId) return;
    import("../domain/savegame").then(({ saveState }) => {
      saveState(state);
      this.scene.start("InventoryScene", { slotId: this.slotId });
    });
  }

  private setMessage(message: string, isError = false): void {
    if (!this.messageText) return;
    this.messageText.setColor(isError ? "#fca5a5" : "#7ee787");
    this.messageText.setText(message);
  }
}
