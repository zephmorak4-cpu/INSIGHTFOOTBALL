from __future__ import annotations

import importlib.util
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
        self.assertIn("INSIGHT FOOTBALL APPROVAL VIDEO", caption)


if __name__ == "__main__":
    unittest.main()
