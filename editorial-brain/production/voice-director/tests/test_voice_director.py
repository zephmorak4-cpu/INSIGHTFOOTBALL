from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "editorial-brain" / "production" / "voice-director" / "src"
sys.path.insert(0, str(SRC))

from voice_director.config import load_config
from voice_director.json_utils import load_json_file
from voice_director.service import VoiceDirectorService

CONFIG = ROOT / "editorial-brain" / "production" / "voice-director" / "config" / "voice-director.config.json"
SCRIPT = ROOT / "editorial-brain" / "output" / "final-script-package.json"


class VoiceDirectorTests(unittest.TestCase):
    def run_service(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(CONFIG), output_directory=Path(temp.name) / "out", log_directory=Path(temp.name) / "logs")
        return VoiceDirectorService(config).run(load_json_file(SCRIPT))

    def test_profile_generation(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertEqual(result["voice_plan"]["voice_profile"], "knowledgeable football friend")

    def test_emotion_mapping(self):
        emotions = {section["source_section"]: section["emotion"] for section in self.run_service()["voice_plan"]["sections"]}
        self.assertEqual(emotions["hook"], "curious")
        self.assertEqual(emotions["cta"], "friendly")

    def test_pacing_validation(self):
        plan = self.run_service()["voice_plan"]
        self.assertGreaterEqual(plan["target_speed_wpm"], 120)
        self.assertLessEqual(plan["target_speed_wpm"], 145)


if __name__ == "__main__":
    unittest.main()
