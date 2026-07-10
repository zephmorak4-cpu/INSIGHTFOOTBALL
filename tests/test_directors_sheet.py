from __future__ import annotations

import unittest

from app.content.directors_sheet import build_directors_sheet


class DirectorsSheetTests(unittest.TestCase):
    def test_directors_sheet_timeline(self):
        sheet = build_directors_sheet({"home_team": "Chelsea", "away_team": "Arsenal", "competition": "Premier League"}, "One sentence. Two sentence. Three sentence. Four sentence.")
        self.assertIn("CapCut", sheet)
        self.assertIn("Moment", sheet)


if __name__ == "__main__":
    unittest.main()
