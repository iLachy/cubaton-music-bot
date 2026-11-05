import json
import tempfile
import unittest
from pathlib import Path

from telegram_message_state import (
    PublicationStateError,
    TelegramMessageState,
)


class TelegramMessageStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "telegram_messages.json"
        self.state = TelegramMessageState(self.path)
        self.key = "k:artista|cancion"
        self.state.ensure_song(
            self.key,
            song_id="video:abc123",
            title="Canción de prueba",
            artists="Artista de prueba",
            video_id="abc123",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cover_and_preview_are_tracked_independently(self):
        self.state.mark_sending(self.key, "cover")
        self.state.mark_sent(self.key, "cover", 101)

        self.assertEqual(
            self.state.get_step(self.key, "cover")["status"],
            "sent",
        )
        self.assertEqual(
            self.state.get_step(self.key, "cover")["message_id"],
            101,
        )
        self.assertEqual(
            self.state.get_step(self.key, "preview")["status"],
            "pending",
        )
        self.assertEqual(self.state.pending_steps(self.key), ["preview"])

    def test_restart_preserves_sent_message_and_pending_step(self):
        self.state.mark_sending(self.key, "cover")
        self.state.mark_sent(self.key, "cover", 202)

        restarted = TelegramMessageState(self.path)

        self.assertEqual(
            restarted.get_step(self.key, "cover")["message_id"],
            202,
        )
        self.assertEqual(restarted.pending_steps(self.key), ["preview"])

    def test_interrupted_send_becomes_unknown_and_is_not_retried(self):
        self.state.mark_sending(self.key, "cover")

        restarted = TelegramMessageState(self.path)

        self.assertEqual(
            restarted.get_step(self.key, "cover")["status"],
            "unknown",
        )
        with self.assertRaises(PublicationStateError):
            restarted.mark_sending(self.key, "cover")

    def test_no_preview_can_be_a_resolved_terminal_state(self):
        self.state.mark_sending(self.key, "cover")
        self.state.mark_sent(self.key, "cover", 303)
        self.state.mark_not_available(
            self.key,
            "preview",
            "No se encontró preview.",
        )

        self.assertTrue(self.state.is_song_complete(self.key))

    def test_incomplete_song_metadata_is_available_for_resume(self):
        metadata = {
            "id": "video:abc123",
            "video_id": "abc123",
            "titulo": "Canción de prueba",
            "artistas": "Artista de prueba",
            "nombre_publicacion": "Single",
            "anio": "2026",
            "youtube_url": "https://music.youtube.com/watch?v=abc123",
        }
        self.state.ensure_song(
            self.key,
            song_id="video:abc123",
            title="Canción de prueba",
            artists="Artista de prueba",
            video_id="abc123",
            song_data=metadata,
        )

        incomplete = self.state.incomplete_songs()

        self.assertEqual(len(incomplete), 1)
        self.assertEqual(incomplete[0][0], self.key)
        self.assertEqual(incomplete[0][1]["titulo"], "Canción de prueba")

    def test_state_file_is_valid_json_after_atomic_save(self):
        self.state.mark_sending(self.key, "cover")

        with self.path.open("r", encoding="utf-8") as handle:
            saved = json.load(handle)

        self.assertEqual(saved["version"], 1)
        self.assertIn(self.key, saved["songs"])


if __name__ == "__main__":
    unittest.main()
