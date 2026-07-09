from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path(r"C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
if not PYTHON.exists():
    PYTHON = Path(sys.executable)


class UrgentProductionEditorGuardTests(unittest.TestCase):
    def run_entrypoint(self, extra_env: dict[str, str] | None = None):
        env = os.environ.copy()
        env.update({"INSIGHT_FOOTBALL_ENV": "production", "INSIGHT_FOOTBALL_RUN_TESTS_ON_RENDER": "false"})
        if extra_env:
            env.update(extra_env)
        return subprocess.run([str(PYTHON), "scripts/render_daily_entrypoint.py"], cwd=ROOT, env=env, text=True, capture_output=True, timeout=60)

    def test_production_fails_if_editor_selection_missing(self):
        env = {"EDITOR_SELECTION_PATH": ""}
        result = self.run_entrypoint(env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EDITOR_SELECTION_REQUIRED", result.stdout)

    def test_production_fails_if_selected_by_is_automatic(self):
        with tempfile.TemporaryDirectory() as tmp:
            selection = Path(tmp) / "editor-selection.json"
            selection.write_text(json.dumps(self.selection(selected_by="automatic_recommendation")), encoding="utf-8")
            result = self.run_entrypoint({"EDITOR_SELECTION_PATH": str(selection)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PRODUCTION_REQUIRES_HUMAN_EDITOR_SELECTION", result.stdout)

    def test_production_passes_editor_guard_for_human_editor(self):
        from scripts.production_editor_guard import load_valid_editor_selection

        selection = load_valid_editor_selection(ROOT / "examples" / "editor-selection-france-morocco.json")
        self.assertEqual(selection["selected_by"], "human_editor")
        self.assertEqual(selection["match"], "France vs Morocco")

    def test_live_builder_uses_editor_selection_without_fixture_api(self):
        import scripts.live_daily_input_builder as builder

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "live-daily-input.json"
            env = {
                "INSIGHT_FOOTBALL_ENV": "production",
                "EDITOR_SELECTION_PATH": str(ROOT / "examples" / "editor-selection-france-morocco.json"),
                "APP_FOOTBALL_API_KEY": "",
                "API_FOOTBALL_API_KEY": "",
            }
            with patch.dict(os.environ, env), patch.object(builder, "fetch_fixtures", side_effect=AssertionError("fixture API must not be called")):
                payload = builder.build_live_daily_input(target_date="2026-07-09", output_path=output)

        self.assertEqual(payload["production_metadata"]["match"], "France vs Morocco")
        self.assertEqual(payload["production_metadata"]["selected_by"], "human_editor")
        self.assertEqual(payload["fixtures"][0]["selection_source"], "human_editor")

    def test_telegram_message_not_sent_without_human_editor_selection(self):
        import scripts.send_telegram_approval as telegram

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "editorial-brain" / "output"
            output.mkdir(parents=True)
            (output / "publish-ready-package.json").write_text(json.dumps({"production_id": "p1", "match": {"home_team": "Qarabag", "away_team": "Vestri"}}), encoding="utf-8")
            with patch.object(telegram, "ROOT", root), patch.object(telegram, "OUTPUT", output), patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_APPROVAL_CHAT_ID": "123"}), patch.object(sys, "argv", ["send_telegram_approval.py"]):
                self.assertEqual(telegram.main(), 1)

    def test_qarabag_vestri_cannot_be_selected_automatically_in_production(self):
        result = self.run_entrypoint({"EDITOR_SELECTION_PATH": ""})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EDITOR_SELECTION_REQUIRED", result.stdout)
        report = json.loads((ROOT / "editorial-brain" / "output" / "daily-run-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["steps"], [])

    def test_warnings_filter_removes_stale_assets_for_france_morocco(self):
        import scripts.send_telegram_approval as telegram

        message_match = {"home_team": "France", "away_team": "Morocco", "competition": "FIFA World Cup"}
        warnings = telegram._clean_warnings([
            "Premier League logo requires rights confirmation.",
            "Liverpool badge requires rights confirmation.",
            "France badge requires rights confirmation.",
            "FIFA World Cup logo requires rights confirmation.",
        ], message_match)
        self.assertIn("France badge requires rights confirmation.", warnings)
        self.assertIn("FIFA World Cup logo requires rights confirmation.", warnings)
        self.assertNotIn("Premier League logo requires rights confirmation.", warnings)
        self.assertFalse(any("Liverpool" in warning for warning in warnings))

    @staticmethod
    def selection(selected_by: str = "human_editor") -> dict[str, str]:
        return {
            "production_id": "if-2026-07-09-france-morocco",
            "production_date": "2026-07-09",
            "selected_by": selected_by,
            "match": "France vs Morocco",
            "home_team": "France",
            "away_team": "Morocco",
            "competition": "FIFA World Cup",
            "kickoff_time": "2026-07-09T21:00:00+01:00",
            "priority": "high",
            "editor_notes": "Use this match for today's INSIGHT FOOTBALL video.",
            "audio_mode": "silent",
            "render_mode": "creatomate",
        }


if __name__ == "__main__":
    unittest.main()
