from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "send_telegram_approval.py"
spec = importlib.util.spec_from_file_location("send_telegram_approval", SCRIPT)
telegram = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["send_telegram_approval"] = telegram
spec.loader.exec_module(telegram)


class TelegramApprovalTests(unittest.TestCase):
    def test_find_approval_video_prefers_real_mp4(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "editorial-brain" / "output"
            output.mkdir(parents=True)
            video = root / "renders" / "final_video.mp4"
            video.parent.mkdir()
            video.write_bytes(b"mp4")
            (output / "publish-ready-package.json").write_text(f'{{"final_video_path": "{video.as_posix()}"}}', encoding="utf-8")
            with patch.object(telegram, "ROOT", root), patch.object(telegram, "OUTPUT", output):
                self.assertEqual(telegram.find_approval_video(), video)

    def test_find_approval_video_rejects_placeholder_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "editorial-brain" / "output"
            output.mkdir(parents=True)
            placeholder = root / "renders" / "final_video.placeholder.json"
            placeholder.parent.mkdir()
            placeholder.write_text("{}", encoding="utf-8")
            (output / "publish-ready-package.json").write_text(f'{{"final_video_path": "{placeholder.as_posix()}"}}', encoding="utf-8")
            with patch.object(telegram, "ROOT", root), patch.object(telegram, "OUTPUT", output):
                self.assertIsNone(telegram.find_approval_video())

    def test_multipart_body_contains_video_field(self):
        with tempfile.TemporaryDirectory() as temp:
            video = Path(temp) / "final_video.mp4"
            video.write_bytes(b"fake mp4")
            body, content_type = telegram._multipart_body({"chat_id": "123", "caption": "Approval"}, "video", video)
            self.assertIn("multipart/form-data", content_type)
            self.assertIn(b'name="video"; filename="final_video.mp4"', body)
            self.assertIn(b"fake mp4", body)

    def test_compact_caption_stays_within_telegram_limit(self):
        caption = telegram.compact_caption("https://github.com/example/run")
        self.assertLessEqual(len(caption), 1024)
        self.assertIn("INSIGHT FOOTBALL PRODUCTION PREVIEW", caption)

    def test_render_not_ready_without_validated_mp4(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "editorial-brain" / "output"
            output.mkdir(parents=True)
            (output / "render-complete-package.json").write_text(json.dumps({"video_status": "failed", "creatomate_status": "failed"}), encoding="utf-8")
            with patch.object(telegram, "ROOT", root), patch.object(telegram, "OUTPUT", output):
                self.assertFalse(telegram.render_ready_for_video())

    def test_failure_alert_does_not_claim_video_completed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "editorial-brain" / "output"
            output.mkdir(parents=True)
            package = {"metadata": {"production_id": "p1"}, "match": {"home_team": "France", "away_team": "Morocco"}, "locked_fields": {"selection_source": "human_editor"}}
            (output / "publish-ready-package.json").write_text(json.dumps(package), encoding="utf-8")
            (output / "render-complete-package.json").write_text(json.dumps({"creatomate_status": "forbidden", "render_status": {"status": "failed", "errors": ["CREATOMATE_ACCESS_FORBIDDEN"]}}), encoding="utf-8")
            (output / "creatomate_connection_report.json").write_text(json.dumps({"http_status": 403, "response_body_safe_excerpt": "Forbidden"}), encoding="utf-8")
            with patch.object(telegram, "ROOT", root), patch.object(telegram, "OUTPUT", output):
                alert = telegram.build_failure_alert()
        self.assertIn("INSIGHT FOOTBALL RENDER FAILURE", alert)
        self.assertNotIn("completed", alert.lower())


if __name__ == "__main__":
    unittest.main()
