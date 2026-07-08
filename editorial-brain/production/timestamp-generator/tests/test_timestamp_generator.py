from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "editorial-brain" / "production"
for folder in ["voice-director", "pronunciation-engine", "ssml-generator", "timestamp-generator"]:
    sys.path.insert(0, str(BASE / folder / "src"))

from pronunciation_engine.config import load_config as load_pron_config
from pronunciation_engine.service import PronunciationEngineService
from ssml_generator.config import load_config as load_ssml_config
from ssml_generator.service import SSMLGeneratorService
from timestamp_generator.config import load_config
from timestamp_generator.service import TimestampGeneratorService
from voice_director.config import load_config as load_voice_config
from voice_director.json_utils import load_json_file
from voice_director.service import VoiceDirectorService

SCRIPT = ROOT / "editorial-brain" / "output" / "final-script-package.json"


def inputs(temp_path: Path):
    script = load_json_file(SCRIPT)
    voice = VoiceDirectorService(replace(load_voice_config(BASE / "voice-director" / "config" / "voice-director.config.json"), output_directory=temp_path, log_directory=temp_path)).run(script)["voice_plan"]
    pron = PronunciationEngineService(replace(load_pron_config(BASE / "pronunciation-engine" / "config" / "pronunciation-engine.config.json"), output_directory=temp_path, log_directory=temp_path)).run(script, voice)["pronunciation_dictionary"]
    ssml = SSMLGeneratorService(replace(load_ssml_config(BASE / "ssml-generator" / "config" / "ssml-generator.config.json"), output_directory=temp_path, log_directory=temp_path)).run(script, voice, pron)["ssml_metadata"]
    return voice, ssml


class TimestampGeneratorTests(unittest.TestCase):
    def run_service(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(BASE / "timestamp-generator" / "config" / "timestamp-generator.config.json"), output_directory=Path(temp.name), log_directory=Path(temp.name))
        return TimestampGeneratorService(config).run(*inputs(Path(temp.name)))

    def test_sentence_timing(self):
        entries = self.run_service()["voice_timestamps"]["entries"]
        self.assertTrue(all(entry["estimated_duration"] > 0 for entry in entries))

    def test_scene_timing(self):
        entries = self.run_service()["voice_timestamps"]["entries"]
        self.assertLess(entries[0]["start"], entries[-1]["end"])

    def test_duration_under_limit(self):
        self.assertLessEqual(self.run_service()["voice_timestamps"]["total_estimated_duration"], 60)


if __name__ == "__main__":
    unittest.main()
