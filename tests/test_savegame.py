import os
import unittest
from tempfile import TemporaryDirectory
from unittest import mock

from core.data import savegame


class SaveGameTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._env_patch = mock.patch.dict(
            os.environ,
            {savegame.SAVE_DIR_ENV: self._tmp.name},
            clear=False,
        )
        self._env_patch.start()
        self.addCleanup(self._env_patch.stop)

    def test_save_and_load_roundtrip(self):
        state = savegame.create_default_state("slot1")
        savegame.save_state(state)

        loaded = savegame.load_state("slot1")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.slot_id, "slot1")
        self.assertEqual(loaded.location_id, state.location_id)
        self.assertEqual(
            [actor.name for actor in loaded.actors],
            [actor.name for actor in state.actors],
        )
        self.assertEqual(loaded.inventory.munny, state.inventory.munny)
        self.assertEqual(loaded.created_at, state.created_at)
        self.assertEqual(loaded.updated_at, state.updated_at)

    def test_list_slots_marks_existing_and_empty(self):
        empty_slots = savegame.list_slots(max_slots=2)
        self.assertEqual(len(empty_slots), 2)
        self.assertFalse(any(slot.exists for slot in empty_slots))

        state = savegame.create_default_state("slot1")
        savegame.save_state(state)

        slots = savegame.list_slots(max_slots=2)
        self.assertTrue(slots[0].exists)
        self.assertEqual(slots[0].slot_id, "slot1")
        self.assertFalse(slots[1].exists)
        self.assertIn(state.actors[0].name, ", ".join(slots[0].party))


if __name__ == "__main__":
    unittest.main()
