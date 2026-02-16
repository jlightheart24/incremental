import Phaser from "phaser";

export type NavTarget = {
  label: string;
  scene: string;
};

export function renderNavBar(
  scene: Phaser.Scene,
  params: {
    current: string;
    slotId?: string | null;
    targets: NavTarget[];
  }
): void {
  const { current, slotId, targets } = params;
  const y = 16;
  const startX = 20;
  let x = startX;

  targets.forEach((target) => {
    const isActive = target.scene === current;
    const text = scene.add
      .text(x, y, target.label, {
        fontFamily: "Arial",
        fontSize: "14px",
        color: isActive ? "#ffffff" : "#cbd5e1",
        backgroundColor: isActive ? "#334155" : "#1f2937",
        padding: { x: 10, y: 6 }
      })
      .setOrigin(0, 0)
      .setInteractive({ useHandCursor: !isActive });

    if (!isActive) {
      text.on("pointerover", () => {
        text.setStyle({ backgroundColor: "#475569", color: "#ffffff" });
      });
      text.on("pointerout", () => {
        text.setStyle({ backgroundColor: "#1f2937", color: "#cbd5e1" });
      });
      text.on("pointerup", () => {
        if (slotId) {
          scene.scene.start(target.scene, { slotId });
        } else {
          scene.scene.start(target.scene);
        }
      });
    }

    x += text.width + 10;
  });
}
