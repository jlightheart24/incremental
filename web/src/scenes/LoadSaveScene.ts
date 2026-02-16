import Phaser from "phaser";
import { createDefaultState, listSlots, loadState, saveState } from "../domain/savegame";

export class LoadSaveScene extends Phaser.Scene {
  private slotTexts: Phaser.GameObjects.Text[] = [];
  private selectedIndex = 0;
  private confirmDelete = false;
  private hintText?: Phaser.GameObjects.Text;
  private detailText?: Phaser.GameObjects.Text;
  private slotsSnapshot?: ReturnType<typeof listSlots>;

  constructor() {
    super("LoadSaveScene");
  }

  create(): void {
    const { width, height } = this.scale;
    const title = this.add
      .text(width * 0.5, 80, "Kingdom Heart 2ˣ - Select a Save Slot", {
        fontFamily: "Arial",
        fontSize: "28px",
        color: "#ffffff"
      })
      .setOrigin(0.5, 0.5);

    const slots = listSlots({ maxSlots: 3 });
    this.slotsSnapshot = slots;
    this.slotTexts = slots.map((slot, index) => {
      const label = slot.exists
        ? `${slot.title} - ${slot.locationDisplay()} - ${slot.party.join(", ")}`
        : `${slot.title} - Empty (Create)`;

      const text = this.add
        .text(width * 0.5, 160 + index * 60, label, {
          fontFamily: "Arial",
          fontSize: "20px",
          color: slot.exists ? "#d4f1ff" : "#9aa0a6",
          backgroundColor: "#111827",
          padding: { x: 14, y: 8 }
        })
        .setOrigin(0.5, 0.5)
        .setInteractive({ useHandCursor: true });

      text.on("pointerover", () => {
        this.selectedIndex = index;
        this.refreshFocus();
      });
      text.on("pointerdown", () => {
        this.selectedIndex = index;
        this.confirmDelete = false;
        this.refreshFocus();
      });
      text.on("pointerup", () => this.handleSlot(index + 1));

      return text;
    });

    this.hintText = this.add
      .text(
        width * 0.5,
        height - 80,
        this.confirmDelete
          ? "Press Del again to confirm delete  |  Esc: Cancel"
          : "Enter: Load  |  1-3: Load  |  Del: Delete  |  Esc: Back",
        {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#cbd5e1"
      }
      )
      .setOrigin(0.5, 0.5);

    this.refreshFocus();
    this.renderDetails();

    this.input.keyboard?.on("keydown-UP", () => {
      this.selectedIndex = (this.selectedIndex - 1 + this.slotTexts.length) % this.slotTexts.length;
      this.confirmDelete = false;
      this.refreshFocus();
      this.refreshHint();
    });
    this.input.keyboard?.on("keydown-DOWN", () => {
      this.selectedIndex = (this.selectedIndex + 1) % this.slotTexts.length;
      this.confirmDelete = false;
      this.refreshFocus();
      this.refreshHint();
    });
    this.input.keyboard?.on("keydown-ENTER", () => this.handleSlot(this.selectedIndex + 1));
    this.input.keyboard?.on("keydown-DELETE", () => this.requestDelete(this.selectedIndex + 1));
    this.input.keyboard?.on("keydown-ESC", () => {
      if (this.confirmDelete) {
        this.confirmDelete = false;
        this.refreshHint();
      } else {
        this.scene.start("MainMenuScene");
      }
    });

    const keys = this.input.keyboard?.addKeys({
      one: Phaser.Input.Keyboard.KeyCodes.ONE,
      two: Phaser.Input.Keyboard.KeyCodes.TWO,
      three: Phaser.Input.Keyboard.KeyCodes.THREE
    });

    if (keys) {
      (keys.one as Phaser.Input.Keyboard.Key).on("down", () => this.handleSlot(1));
      (keys.two as Phaser.Input.Keyboard.Key).on("down", () => this.handleSlot(2));
      (keys.three as Phaser.Input.Keyboard.Key).on("down", () => this.handleSlot(3));
    }
  }

  private handleSlot(slotIndex: number): void {
    const slotId = `slot${slotIndex}`;
    let state = loadState(slotId);
    if (!state) {
      state = createDefaultState(slotId);
      saveState(state);
    }
    this.scene.start("GameScene", { slotId });
  }

  // Single click loads.

  private requestDelete(slotIndex: number): void {
    if (!this.confirmDelete) {
      this.confirmDelete = true;
      this.refreshHint();
      return;
    }
    this.confirmDelete = false;
    const slotId = `slot${slotIndex}`;
    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.removeItem(`incremental_save:${slotId}`);
    }
    this.scene.start("LoadSaveScene");
  }

  private refreshHint(): void {
    if (!this.hintText) return;
    this.hintText.setText(
      this.confirmDelete
        ? "Press Del again to confirm delete  |  Esc: Cancel"
        : "Enter: Load  |  1-3: Load  |  Del: Delete  |  Esc: Back"
    );
  }

  private refreshFocus(): void {
    this.slotTexts.forEach((text, index) => {
      text.setStyle({
        backgroundColor: index === this.selectedIndex ? "#334155" : "#111827",
        color: index === this.selectedIndex ? "#ffffff" : text.style.color
      });
    });
    this.renderDetails();
  }

  private renderDetails(): void {
    if (!this.slotsSnapshot) return;
    const slot = this.slotsSnapshot[this.selectedIndex];
    const { width } = this.scale;
    if (!this.detailText) {
      this.detailText = this.add
        .text(width * 0.7, 160, "", {
          fontFamily: "Arial",
          fontSize: "16px",
          color: "#dce3ea",
          align: "left",
          lineSpacing: 6,
          wordWrap: { width: 360 }
        })
        .setOrigin(0, 0);
    }

    if (!slot) return;
    const lines: string[] = [];
    lines.push(slot.title);
    lines.push(slot.exists ? "Status: Occupied" : "Status: Empty");
    if (slot.exists) {
      lines.push(`Location: ${slot.locationDisplay()}`);
      lines.push(`Party: ${slot.party.join(", ") || "(unknown)"}`);
      lines.push(`Munny: ${slot.munny}`);
      if (slot.updatedAt) {
        lines.push(`Updated: ${slot.updatedAt.toLocaleString()}`);
      }
    }
    this.detailText.setText(lines.join("\n"));
  }
}
