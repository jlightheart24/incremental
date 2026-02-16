import Phaser from "phaser";

export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload(): void {
    // Placeholder for asset loading. We'll wire assets as we port scenes.
  }

  create(): void {
    this.scene.start("MainMenuScene");
  }
}
