from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "send_telegram_approval.py"
sys.path.insert(0, str(ROOT / "scripts"))

import send_telegram_approval as telegram


class Sprint14TelegramTests(unittest.TestCase):
    def test_approval_message_uses_current_editorial_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "editorial-brain" / "output"
            output.mkdir(parents=True)
            package = {
                "metadata": {"production_id": "if-france-morocco"},
                "match": {"home_team": "France", "away_team": "Morocco", "competition": "International Friendly"},
                "story_angle": "France control against Morocco transitions.",
                "central_question": "Can Morocco break France's control?",
                "warnings": ["Liverpool badge requires rights confirmation.", "manual review assets present", "manual review assets present"],
                "locked_fields": {"selection_source": "human_editor"},
            }
            package_path = output / "editorial-package-if-france-morocco.json"
            package_path.write_text(json.dumps(package), encoding="utf-8")
            (output / "daily-run-report.json").write_text(json.dumps({"success": True, "steps": [{"name": "editorial_orchestrator", "stdout": json.dumps({"package_path": str(package_path)})}]}), encoding="utf-8")
            (output / "publish_readiness_report.json").write_text(json.dumps({"final_status": "needs_human_review", "overall_score": 86, "warnings": ["manual review assets present"]}), encoding="utf-8")
            (output / "publishing_report.json").write_text(json.dumps({"dry_run": True}), encoding="utf-8")
            (output / "render-complete-package.json").write_text(json.dumps({"renderer_profile": "creatomate", "render_audio_mode": "silent", "creatomate_status": "dry_run_complete", "render_status": {"status": "completed"}}), encoding="utf-8")
            with patch.object(telegram, "ROOT", root), patch.object(telegram, "OUTPUT", output):
                message = telegram.build_message("")
        self.assertIn("Match: France vs Morocco", message)
        self.assertIn("Selected by: Human editor", message)
        self.assertIn("Audio mode: silent, ready for CapCut voice/audio overlay", message)
        self.assertIn("Creatomate status: dry_run_complete", message)
        self.assertNotIn("Liverpool badge", message)
        self.assertEqual(message.count("manual review assets present"), 1)


if __name__ == "__main__":
    unittest.main()
