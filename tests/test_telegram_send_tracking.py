import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot
from telegram_message_state import TelegramMessageState


def telegram_response(message_id=777, status_code=200, ok=True):
    payload = {
        "ok": ok,
        "result": {"message_id": message_id} if ok else {},
    }
    return SimpleNamespace(
        ok=ok,
        status_code=status_code,
        text="mock Telegram response",
        json=lambda: payload,
    )


class TelegramSendTrackingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state = TelegramMessageState(
            Path(self.temp_dir.name) / "telegram_messages.json"
        )
        self.key = "k:artist|track"
        self.state.ensure_song(
            self.key,
            song_id="video:track123",
            title="Track",
            artists="Artist",
            video_id="track123",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("bot.requests.post")
    def test_text_cover_records_message_id(self, post):
        post.return_value = telegram_response(501)

        result = bot.enviar_sin_portada(
            "caption",
            None,
            self.state,
            self.key,
        )

        self.assertEqual(result, (True, 501, None))
        self.assertEqual(
            self.state.get_step(self.key, "cover")["message_id"],
            501,
        )

    @patch("bot.requests.post")
    def test_audio_preview_records_message_id(self, post):
        post.return_value = telegram_response(502)
        preview = {
            "bytes": b"audio-bytes",
            "extension": "m4a",
            "mime": "audio/mp4",
            "fuente": "Apple Music",
        }

        result = bot.enviar_preview_audio(
            {
                "titulo": "Track",
                "artistas": "Artist",
                "video_id": "track123",
                "youtube_url": "https://music.youtube.com/watch?v=track123",
            },
            preview,
            self.state,
            self.key,
        )

        self.assertEqual(result, (True, 502, None))
        self.assertEqual(
            self.state.get_step(self.key, "preview")["message_id"],
            502,
        )

    @patch("bot.requests.post")
    def test_http_4xx_is_retryable_failure(self, post):
        post.return_value = telegram_response(ok=False, status_code=400)

        result = bot.enviar_sin_portada(
            "caption",
            None,
            self.state,
            self.key,
        )

        self.assertFalse(result[0])
        self.assertEqual(
            self.state.get_step(self.key, "cover")["status"],
            "failed",
        )

    @patch("bot.requests.post")
    def test_http_5xx_is_unknown_and_not_automatically_retryable(self, post):
        post.return_value = telegram_response(ok=False, status_code=500)

        result = bot.enviar_sin_portada(
            "caption",
            None,
            self.state,
            self.key,
        )

        self.assertFalse(result[0])
        self.assertEqual(
            self.state.get_step(self.key, "cover")["status"],
            "unknown",
        )


if __name__ == "__main__":
    unittest.main()
