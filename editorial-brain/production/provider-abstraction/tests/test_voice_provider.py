from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "editorial-brain" / "production" / "provider-abstraction" / "src"
sys.path.insert(0, str(SRC))

from voice_provider import get_provider, list_supported_providers


class VoiceProviderTests(unittest.TestCase):
    def test_required_providers_exist(self):
        providers = set(list_supported_providers())
        self.assertTrue({"google_cloud_tts", "azure_speech", "elevenlabs", "openai_tts", "cartesia", "playht"}.issubset(providers))

    def test_ssml_validation(self):
        result = get_provider("openai_tts").validate_ssml("<speak><s>Hello</s></speak>")
        self.assertTrue(result.success)

    def test_generation_is_metadata_only(self):
        result = get_provider("elevenlabs").generate_voice("<speak>Hello</speak>", "voice", "out.mp3")
        self.assertFalse(result.success)
        self.assertIn("disabled", result.message)


if __name__ == "__main__":
    unittest.main()
