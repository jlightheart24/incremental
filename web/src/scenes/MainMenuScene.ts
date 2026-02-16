import Phaser from "phaser";

export class MainMenuScene extends Phaser.Scene {
  constructor() {
    super("MainMenuScene");
  }

  create(): void {
    const { width, height } = this.scale;

    this.add
      .text(width * 0.5, 120, "Kingdom Heart 2ˣ", {
        fontFamily: "Arial",
        fontSize: "32px",
        color: "#ffffff"
      })
      .setOrigin(0.5, 0.5);

    const buttonY = height * 0.5;
    const buttonStyle = {
      fontFamily: "Arial",
      fontSize: "22px",
      color: "#dce3ea",
      backgroundColor: "#1f2937",
      padding: { x: 16, y: 10 }
    } as const;

    const startButton = this.add
      .text(width * 0.5, buttonY - 40, "Start", buttonStyle)
      .setOrigin(0.5, 0.5)
      .setInteractive({ useHandCursor: true });

    const loadButton = this.add
      .text(width * 0.5, buttonY + 20, "Load Save", buttonStyle)
      .setOrigin(0.5, 0.5)
      .setInteractive({ useHandCursor: true });

    const setButtonState = (button: Phaser.GameObjects.Text, focused: boolean) => {
      button.setStyle({
        backgroundColor: focused ? "#334155" : "#1f2937",
        color: focused ? "#ffffff" : "#dce3ea"
      });
    };

    let focusedIndex = 0;
    const buttons = [startButton, loadButton];
    const refreshFocus = () => {
      buttons.forEach((button, index) => setButtonState(button, index === focusedIndex));
    };

    refreshFocus();

    buttons.forEach((button, index) => {
      button.on("pointerover", () => {
        focusedIndex = index;
        refreshFocus();
      });
      button.on("pointerout", () => refreshFocus());
    });

    startButton.on("pointerup", () => this.scene.start("LoadSaveScene"));
    loadButton.on("pointerup", () => this.scene.start("LoadSaveScene"));

    this.add
      .text(width * 0.5, height - 120, "Enter: Start  |  L: Load  |  Esc: Quit", {
        fontFamily: "Arial",
        fontSize: "16px",
        color: "#9aa0a6"
      })
      .setOrigin(0.5, 0.5);

    this.input.keyboard?.on("keydown-ENTER", () => {
      buttons[focusedIndex].emit("pointerup");
    });
    this.input.keyboard?.on("keydown-L", () => {
      this.scene.start("LoadSaveScene");
    });
    this.input.keyboard?.on("keydown-UP", () => {
      focusedIndex = (focusedIndex - 1 + buttons.length) % buttons.length;
      refreshFocus();
    });
    this.input.keyboard?.on("keydown-DOWN", () => {
      focusedIndex = (focusedIndex + 1) % buttons.length;
      refreshFocus();
    });
    this.input.keyboard?.on("keydown-ESC", () => {
      this.game.destroy(true);
    });
  }
}
