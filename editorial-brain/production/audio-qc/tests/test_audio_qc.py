from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "editorial-brain" / "production"
for folder in ["voice-director", "pronunciation-engine", "ssml-generator", "timestamp-generator", "audio-qc"]:
    sys.path.insert(0, str(BASE / folder / "src"))

from audio_qc.config import load_config
from audio_qc.service import AudioQCService
from pronunciation_engine.config import load_config as load_pron_config
from pronunciation_engine.service import PronunciationEngineService
from ssml_generator.config import load_config as load_ssml_config
from ssml_generator.service import SSMLGeneratorService
from timestamp_generator.config import load_config as load_timestamp_config
from timestamp_generator.service import TimestampGeneratorService
from voice_director.config import load_config as load_voice_config
from voice_director.json_utils import load_json_file
from voice_director.service import VoiceDirectorService

SCRIPT = ROOT / "editorial-brain" / "output" / "final-script-package.json"


def inputs(temp_path: Path):
    script = load_json_file(SCRIPT)
    voice = VoiceDirectorService(replace(load_voice_config(BASE / "voice-director" / "config" / "voice-director.config.json"), output_directory=temp_path, log_directory=temp_path)).run(script)["voice_plan"]
    pron = PronunciationEngineService(replace(load_pron_config(BASE / "pronunciation-engine" / "config" / "pronunciation-engine.config.json"), output_directory=temp_path, log_directory=temp_path)).run(script, voice)["pronunciation_dictionary"]
    ssml_result = SSMLGeneratorService(replace(load_ssml_config(BASE / "ssml-generator" / "config" / "ssml-generator.config.json"), output_directory=temp_path, log_directory=temp_path)).run(script, voice, pron)
    stamps = TimestampGeneratorService(replace(load_timestamp_config(BASE / "timestamp-generator" / "config" / "timestamp-generator.config.json"), output_directory=temp_path, log_directory=temp_path)).run(voice, ssml_result["ssml_metadata"])["voice_timestamps"]
    return voice, pron, ssml_result["ssml"], ssml_result["ssml_metadata"], stamps


class AudioQCTests(unittest.TestCase):
    def run_service(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(BASE / "audio-qc" / "config" / "audio-qc.config.json"), output_directory=Path(temp.name), log_directory=Path(temp.name))
        return AudioQCService(config).run(*inputs(Path(temp.name)))

    def test_duration(self):
        report = self.run_service()["audio_qc_report"]
        self.assertLessEqual(report["estimated_duration_seconds"], 60)

    def test_pacing(self):
        report = self.run_service()["audio_qc_report"]
        self.assertGreaterEqual(report["estimated_wpm"], 120)
        self.assertLessEqual(report["estimated_wpm"], 145)

    def test_naturalness(self):
        self.assertGreaterEqual(self.run_service()["audio_qc_report"]["naturalness"], 85)

    def test_voice_production_package_validates(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertEqual(result["voice_production_package"]["approval_status"], "approved")


if __name__ == "__main__":
    unittest.main()
