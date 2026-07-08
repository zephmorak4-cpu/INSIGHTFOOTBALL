from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "editorial-brain" / "production"
for folder in ["voice-director", "pronunciation-engine", "ssml-generator"]:
    sys.path.insert(0, str(BASE / folder / "src"))

from pronunciation_engine.config import load_config as load_pron_config
from pronunciation_engine.service import PronunciationEngineService
from ssml_generator.config import load_config
from ssml_generator.service import SSMLGeneratorService
from voice_director.config import load_config as load_voice_config
from voice_director.json_utils import load_json_file
from voice_director.service import VoiceDirectorService

SCRIPT = ROOT / "editorial-brain" / "output" / "final-script-package.json"


def inputs(temp_path: Path):
    script = load_json_file(SCRIPT)
    voice = VoiceDirectorService(replace(load_voice_config(BASE / "voice-director" / "config" / "voice-director.config.json"), output_directory=temp_path, log_directory=temp_path)).run(script)["voice_plan"]
    pron = PronunciationEngineService(replace(load_pron_config(BASE / "pronunciation-engine" / "config" / "pronunciation-engine.config.json"), output_directory=temp_path, log_directory=temp_path)).run(script, voice)["pronunciation_dictionary"]
    return script, voice, pron


class SSMLGeneratorTests(unittest.TestCase):
    def run_service(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(BASE / "ssml-generator" / "config" / "ssml-generator.config.json"), output_directory=Path(temp.name), log_directory=Path(temp.name))
        return SSMLGeneratorService(config).run(*inputs(Path(temp.name)))

    def test_valid_ssml(self):
        self.assertTrue(self.run_service()["success"])

    def test_emphasis(self):
        self.assertIn("<emphasis", self.run_service()["ssml"])

    def test_breaks(self):
        self.assertIn("<break", self.run_service()["ssml"])


if __name__ == "__main__":
    unittest.main()
