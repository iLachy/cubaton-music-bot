import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bot


class ReleaseStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "releases.json"
        self.patch_state_file = patch.object(bot, "STATE_FILE", str(self.path))
        self.patch_state_file.start()

    def tearDown(self):
        self.patch_state_file.stop()
        self.temp_dir.cleanup()

    def test_missing_file_is_the_only_case_that_returns_none(self):
        self.assertIsNone(bot.cargar_estado())

    def test_corrupt_json_fails_closed(self):
        self.path.write_text("{not-json", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            bot.cargar_estado()

    def test_unsupported_version_fails_closed(self):
        self.path.write_text(
            json.dumps({"version": 999, "canciones": []}),
            encoding="utf-8",
        )
        with self.assertRaises(RuntimeError):
            bot.cargar_estado()

    def test_invalid_song_list_fails_closed(self):
        self.path.write_text(
            json.dumps({"version": bot.ESTADO_VERSION, "canciones": "bad"}),
            encoding="utf-8",
        )
        with self.assertRaises(RuntimeError):
            bot.cargar_estado()

    def test_atomic_save_can_be_loaded_back(self):
        state = {
            "version": bot.ESTADO_VERSION,
            "canciones": {"video:xyz", "k:artist|title"},
        }
        bot.guardar_estado(state)

        loaded = bot.cargar_estado()
        self.assertEqual(
            loaded["canciones"],
            {"video:xyz", "k:artist|title"},
        )
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["version"], 2)

    def test_state_write_failure_is_not_silent(self):
        with patch("bot.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(RuntimeError):
                bot.guardar_estado({"canciones": {"video:abc"}})


if __name__ == "__main__":
    unittest.main()
