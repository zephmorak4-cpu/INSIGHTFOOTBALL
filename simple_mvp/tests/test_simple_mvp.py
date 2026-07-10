from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from simple_mvp.ai_editor import validate_content_package
from simple_mvp.asset_resolver import resolve_assets
from simple_mvp.errors import MVPError
from simple_mvp.match_data_fetcher import fetch_match_data
from simple_mvp.qc import run_qc
from simple_mvp.run_production import load_manual_input


def selection() -> dict[str, str]:
    return {
        "production_id": "if-2026-07-10-spain-belgium",
        "match": "Spain vs Belgium",
        "home_team": "Spain",
        "away_team": "Belgium",
        "competition": "FIFA World Cup",
        "stage": "Quarter-final",
        "kickoff_time": "2026-07-10T20:00:00+01:00",
        "selected_by": "human_editor",
        "audio_mode": "silent_capcut",
    }


def content(script_words: int = 125) -> dict[str, object]:
    script = " ".join(["Spain"] + ["Belgium"] + ["specific"] * (script_words - 2))
    return {
        "match": "Spain vs Belgium",
        "competition": "FIFA World Cup",
        "central_question": "Can Belgium slow Spain without losing their own threat?",
        "hook": "This quarter-final is about control against bursts.",
        "main_story": "Spain want rhythm, Belgium want the moment that breaks it.",
        "evidence_points": ["Spain identity verified.", "Belgium identity verified."],
        "balanced_conclusion": "The match should swing on who manages pressure better.",
        "final_cta": "Follow INSIGHT FOOTBALL for the next read before kickoff.",
        "full_script": script,
        "visual_scenes": [{"duration": 7, "text": "x", "visual": "x", "assets": [], "animation": "motion", "template_key": f"s{i}"} for i in range(8)],
    }


class SimpleMVPTests(unittest.TestCase):
    def test_manual_input_requires_human_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manual.json"
            payload = selection()
            payload["selected_by"] = "automatic"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(MVPError) as ctx:
                load_manual_input(path)
        self.assertEqual(ctx.exception.code, "HUMAN_SELECTION_REQUIRED")

    def test_match_data_fetcher_stops_without_real_sources(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(MVPError) as ctx:
                fetch_match_data(selection())
        self.assertEqual(ctx.exception.code, "INSUFFICIENT_REAL_MATCH_DATA")

    def test_content_validation_rejects_sample_leakage(self):
        package = content()
        package["full_script"] += " Liverpool Arsenal"
        issues = validate_content_package(package, selection())
        self.assertTrue(any("sample leakage" in issue for issue in issues))

    def test_asset_resolver_never_uses_liverpool_or_arsenal(self):
        assets = resolve_assets(selection())
        text = json.dumps(assets)
        self.assertNotIn("Liverpool", text)
        self.assertNotIn("Arsenal", text)

    def test_qc_passes_minimal_valid_package(self):
        with tempfile.TemporaryDirectory() as temp:
            video = Path(temp) / "final_video.mp4"
            video.write_bytes(b"mp4")
            report = run_qc(selection(), content(), {"brand_logo": "https://example.com/logo.png"}, {"final_video_path": str(video), "resolution": "1080x1920", "duration_seconds": 60}, {"video_sent": True})
        self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
