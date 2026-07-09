from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "editorial-brain" / "editor-match-selector" / "src"))
sys.path.insert(0, str(ROOT / "editorial-brain" / "match-selector" / "src"))

from editor_match_selector import apply_editor_selection
from match_selector.llm import RuleBasedMatchSelectorClient


class EditorMatchSelectorTests(unittest.TestCase):
    def selection(self):
        return {
            "production_id": "if-2026-07-09-france-morocco",
            "production_date": "2026-07-09",
            "selected_by": "human_editor",
            "match": "France vs Morocco",
            "home_team": "France",
            "away_team": "Morocco",
            "competition": "FIFA World Cup",
            "kickoff_time": "2026-07-09T21:00:00+01:00",
            "priority": "high",
            "story_angle_optional": "France control against Morocco transitions.",
            "editor_notes": "Use editor pick.",
            "audio_mode": "silent",
            "render_mode": "creatomate",
        }

    def test_editor_selected_france_morocco_is_used(self):
        daily = {"production_metadata": {"date": "2026-07-09"}, "fixtures": []}
        updated = apply_editor_selection(daily, self.selection())
        self.assertEqual(updated["fixtures"][0]["home_team"], "France")
        self.assertEqual(updated["production_metadata"]["match"], "France vs Morocco")

    def test_automatic_selector_does_not_override_editor(self):
        daily = {
            "production_metadata": {"date": "2026-07-09"},
            "fixtures": [
                {"home_team": "Qarabag", "away_team": "Vestri", "competition": "UEFA Europa League", "kickoff_time": "2026-07-09T18:00:00+00:00", "country": "World", "audience_interest": 1, "importance": 1, "rivalry": 1, "available_data": 1, "story_potential": 1}
            ],
        }
        updated = apply_editor_selection(daily, self.selection())
        selected = RuleBasedMatchSelectorClient(updated).generate("", temperature=0.1, max_tokens=1000)
        self.assertIn('"home_team": "France"', selected)
        self.assertNotIn('"home_team": "Qarabag"', selected.split('"selected_match"')[1].split('"selected_reason"')[0])

    def test_low_profile_match_not_chosen_when_editor_selection_exists(self):
        daily = {"production_metadata": {"date": "2026-07-09"}, "fixtures": [{"home_team": "Transport United", "away_team": "Bhutan U19", "competition": "Premier League", "kickoff_time": "2026-07-09T12:00:00+00:00", "country": "Bhutan", "audience_interest": 9, "importance": 9, "rivalry": 9, "available_data": 9, "story_potential": 9}]}
        updated = apply_editor_selection(daily, self.selection())
        selected = RuleBasedMatchSelectorClient(updated).generate("", temperature=0.1, max_tokens=1000)
        self.assertIn('"away_team": "Morocco"', selected)


if __name__ == "__main__":
    unittest.main()
