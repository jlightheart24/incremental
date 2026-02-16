import { describe, expect, test } from "vitest";
import { createDefaultState, listSlots, loadState, MemoryStorage, saveState } from "../savegame";


describe("Savegame", () => {
  test("save and load roundtrip", () => {
    const storage = new MemoryStorage();
    const state = createDefaultState("slot1");
    saveState(state, { storage });

    const loaded = loadState("slot1", { storage });
    expect(loaded).not.toBeNull();
    if (!loaded) return;

    expect(loaded.slotId).toBe("slot1");
    expect(loaded.locationId).toBe(state.locationId);
    expect(loaded.actors.map((actor) => actor.name)).toEqual(state.actors.map((actor) => actor.name));
    expect(loaded.inventory.munny).toBe(state.inventory.munny);
    expect(loaded.createdAt?.toISOString()).toBe(state.createdAt?.toISOString());
    expect(loaded.updatedAt?.toISOString()).toBe(state.updatedAt?.toISOString());
  });

  test("list slots marks existing and empty", () => {
    const storage = new MemoryStorage();
    const emptySlots = listSlots({ maxSlots: 2, storage });
    expect(emptySlots.length).toBe(2);
    expect(emptySlots.some((slot) => slot.exists)).toBe(false);

    const state = createDefaultState("slot1");
    saveState(state, { storage });

    const slots = listSlots({ maxSlots: 2, storage });
    expect(slots[0].exists).toBe(true);
    expect(slots[0].slotId).toBe("slot1");
    expect(slots[1].exists).toBe(false);
    expect(slots[0].party.join(", ")).toContain(state.actors[0].name);
  });
});
