from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "editorial-brain" / "production" / "rendering-engine" / "shared"))

from rendering_engine.core import CreatomateAdapter, _creatomate_registry


def package() -> dict:
    return {
        "production_id": "if-2026-07-09-france-morocco",
        "match": {"home_team": "France", "away_team": "Morocco", "competition": "International Friendly", "kickoff_time": "2026-07-09T20:00:00+01:00"},
        "competition": "International Friendly",
        "story_angle": "France control against Morocco transitions.",
        "central_question": "Can Morocco break France's control?",
        "surprising_fact": "Morocco's transitions can change the rhythm quickly.",
        "insight_summary": "France need control; Morocco need speed.",
        "primary_evidence": [{"claim": "France control possession.", "simple_translation": "France can slow the game down."}],
        "secondary_evidence": [{"claim": "Morocco counter quickly.", "simple_translation": "Morocco can hurt teams in space."}],
        "viewer_takeaway": "Watch the first midfield turnovers.",
        "timeline": {"total_duration_seconds": 45, "scenes": [{"scene_id": "s1", "caption_text": "France vs Morocco", "asset_refs": [], "duration_seconds": 4, "template_id": "match_intro"}]},
        "caption_sync": {"captions": [{"caption_id": "c1", "text": "France vs Morocco"}]},
        "required_audio": [],
        "render_plan": {"output_settings": {}},
        "required_assets": [],
        "required_fonts": [],
    }


class CreatomateAdapterTests(unittest.TestCase):
    def test_dry_run_payload_builds(self):
        payload = CreatomateAdapter().build_render_payload(package())
        self.assertEqual(payload["renderer"], "creatomate")
        self.assertEqual(payload["variables"]["home_team"], "France")
        self.assertEqual(payload["render_audio_mode"], "silent")
        self.assertFalse(payload["validation"]["issues"])

    def test_live_mode_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            result = CreatomateAdapter().validate_package(package(), dry_run=False)
        self.assertFalse(result["success"])
        self.assertIn("CREATOMATE_API_KEY", result["error"])

    def test_required_variables_validated(self):
        bad = package()
        bad["central_question"] = ""
        payload = CreatomateAdapter().build_render_payload(bad)
        self.assertIn("central_question", "; ".join(payload["validation"]["issues"]))

    def test_registry_has_all_template_keys(self):
        keys = {item["template_key"] for item in _creatomate_registry()["templates"]}
        self.assertTrue({"opening_sting", "match_intro", "central_question", "evidence_card", "tactical_board", "team_comparison", "insight_dashboard", "cta_card", "closing_sting"}.issubset(keys))

    def test_no_sample_leakage_for_france_morocco(self):
        payload = CreatomateAdapter().build_render_payload(package())
        text = str(payload)
        self.assertNotIn("Liverpool", text)
        self.assertNotIn("Arsenal", text)
        self.assertIn("France", text)
        self.assertIn("Morocco", text)


if __name__ == "__main__":
    unittest.main()
