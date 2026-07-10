from __future__ import annotations

import unittest

from app.models.football_models import Fixture
from app.telegram.formatter import format_match_found


class TelegramFormattingTests(unittest.TestCase):
    def test_match_found_format(self):
        text = format_match_found(Fixture("1", "Chelsea", "Arsenal", "Premier League", "2099", "Bridge", "NS", "API"), "run1")
        self.assertIn("MATCH FOUND", text)
        self.assertIn("run1", text)


if __name__ == "__main__":
    unittest.main()
