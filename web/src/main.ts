import Phaser from "phaser";
import {
  BootScene,
  CombatDemoScene,
  GameScene,
  InventoryScene,
  LoadSaveScene,
  MainMenuScene,
  PartyScene,
  MapScene
} from "./scenes";

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: "app",
  backgroundColor: "#0e0f12",
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    width: 1280,
    height: 720
  },
  scene: [
    BootScene,
    MainMenuScene,
    LoadSaveScene,
    GameScene,
    CombatDemoScene,
    InventoryScene,
    PartyScene,
    MapScene
  ]
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const game = new Phaser.Game(config);
