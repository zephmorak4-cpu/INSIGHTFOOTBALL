from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.live_daily_input_builder import build_live_daily_input, normalize_fixtures


class LiveDailyInputBuilderTests(unittest.TestCase):
    def test_normalizes_api_football_fixture(self):
        raw = {
            "response": [
                {
                    "fixture": {"date": "2026-07-09T19:00:00+00:00"},
                    "league": {"name": "Premier League", "country": "England"},
                    "teams": {"home": {"name": "Arsenal"}, "away": {"name": "Chelsea"}},
                }
            ]
        }
        fixtures = normalize_fixtures(raw, "2026-07-09")
        self.assertEqual(fixtures[0]["home_team"], "Arsenal")
        self.assertGreaterEqual(fixtures[0]["importance"], 9)

    def test_builds_from_fixture_file_without_examples(self):
        raw = {
            "fixtures": [
                {
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "competition": "Premier League",
                    "kickoff_time": "2026-07-09T19:00:00+00:00",
                    "country": "England",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "fixtures.json"
            output = Path(temp) / "daily.json"
            source.write_text(json.dumps(raw), encoding="utf-8")
            with patch.dict(os.environ, {"INSIGHT_FOOTBALL_FIXTURES_FILE": str(source)}, clear=False):
                payload = build_live_daily_input(target_date="2026-07-09", output_path=output)
            self.assertTrue(output.exists())
            self.assertEqual(payload["production_metadata"]["input_source"], "live_football_api")
            self.assertFalse(payload["data_availability_notes"]["sample_matches_allowed"])


if __name__ == "__main__":
    unittest.main()
