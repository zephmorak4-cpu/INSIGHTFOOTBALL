from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "editorial-brain" / "production" / "voice-pipeline" / "shared"))

from voice_pipeline import align_speech_to_scenes, clean_voice, process_voice, sync_voice_to_timeline, validate_voice_input


class VoicePipelineTests(unittest.TestCase):
    def test_human_recorded_wav_input_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "voice.wav"
            audio.write_bytes(b"audio")
            report = validate_voice_input(audio)
        self.assertEqual(report["approval_status"], "approved")

    def test_unsupported_format_blocks(self):
        report = validate_voice_input("voice.txt")
        self.assertEqual(report["approval_status"], "blocked")

    def test_alignment_and_sync_contract(self):
        storyboard = {"scenes": [{"scene_id": "scene-01", "voiceover_text": "A short line for the opening."}]}
        timeline = {"scenes": [{"scene_id": "scene-01", "start_time_seconds": 0, "end_time_seconds": 3}]}
        input_report = {"audio_path": "voice.mp3", "approval_status": "approved"}
        alignment = align_speech_to_scenes(clean_voice(process_voice(input_report)), storyboard)
        sync = sync_voice_to_timeline(alignment, timeline)
        self.assertTrue(sync["timeline_auto_adjust"])
        self.assertTrue(sync["captions_from_narration"])


if __name__ == "__main__":
    unittest.main()
