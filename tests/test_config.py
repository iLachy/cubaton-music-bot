import importlib
import os
import unittest
from unittest.mock import patch

import config


class AlertChatConfigurationTests(unittest.TestCase):
    def tearDown(self):
        importlib.reload(config)

    def test_primary_alert_secret_is_read(self):
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_ALERT_CHAT_ID": "-100123456789",
                "TELEGRAM_CHAT_ID": "-100000000000",
            },
            clear=True,
        ):
            importlib.reload(config)
            self.assertEqual(
                config.TELEGRAM_ALERT_CHAT_ID,
                "-100123456789",
            )

    def test_legacy_alert_secret_name_remains_supported(self):
        with patch.dict(
            os.environ,
            {"TELEGRAM_CHAT_ID": "-100987654321"},
            clear=True,
        ):
            importlib.reload(config)
            self.assertEqual(
                config.TELEGRAM_ALERT_CHAT_ID,
                "-100987654321",
            )


if __name__ == "__main__":
    unittest.main()
