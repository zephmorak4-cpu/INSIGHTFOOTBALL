from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VD_SRC = ROOT / "editorial-brain" / "production" / "voice-director" / "src"
SRC = ROOT / "editorial-brain" / "production" / "pronunciation-engine" / "src"
for path in [VD_SRC, SRC]:
    sys.path.insert(0, str(path))

from pronunciation_engine.config import load_config
from pronunciation_engine.service import PronunciationEngineService
from voice_director.config import load_config as load_voice_config
from voice_director.json_utils import load_json_file
from voice_director.service import VoiceDirectorService

BASE = ROOT / "editorial-brain" / "production"
SCRIPT = ROOT / "editorial-brain" / "output" / "final-script-package.json"


class PronunciationEngineTests(unittest.TestCase):
    def run_service(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        script = load_json_file(SCRIPT)
        voice_config = replace(load_voice_config(BASE / "voice-director" / "config" / "voice-director.config.json"), output_directory=Path(temp.name) / "out", log_directory=Path(temp.name) / "logs")
        voice_plan = VoiceDirectorService(voice_config).run(script)["voice_plan"]
        config = replace(load_config(BASE / "pronunciation-engine" / "config" / "pronunciation-engine.config.json"), output_directory=Path(temp.name) / "out", log_directory=Path(temp.name) / "logs")
        return PronunciationEngineService(config).run(script, voice_plan)

    def test_football_names(self):
        terms = {item["term"] for item in self.run_service()["pronunciation_dictionary"]["items"]}
        self.assertIn("Liverpool", terms)
        self.assertIn("Arsenal", terms)

    def test_abbreviations(self):
        items = self.run_service()["pronunciation_dictionary"]["items"]
        self.assertFalse(any(item["term"] == "x-factor" for item in items))

    def test_competition_names(self):
        terms = {item["term"] for item in self.run_service()["pronunciation_dictionary"]["items"]}
        self.assertIn("Premier League", terms)


if __name__ == "__main__":
    unittest.main()
