from __future__ import annotations

import re
from xml.etree import ElementTree

from .base import ProviderResult, VoiceProvider


class MetadataOnlyProvider(VoiceProvider):
    def __init__(self, provider_name: str, voices: list[dict]):
        self.provider_name = provider_name
        self._voices = voices

    def generate_voice(self, ssml: str, voice_id: str, output_path: str) -> ProviderResult:
        return ProviderResult(
            provider=self.provider_name,
            success=False,
            message="Audio generation is intentionally disabled in Sprint 7; this provider exposes compatibility only.",
            payload={"voice_id": voice_id, "output_path": output_path, "ssml_characters": len(ssml)},
        )

    def list_voices(self) -> list[dict]:
        return list(self._voices)

    def validate_ssml(self, ssml: str) -> ProviderResult:
        try:
            ElementTree.fromstring(ssml)
        except ElementTree.ParseError as exc:
            return ProviderResult(self.provider_name, False, f"Invalid SSML: {exc}", {})
        return ProviderResult(self.provider_name, True, "SSML is well-formed.", {"supported_tags": ["speak", "p", "s", "break", "emphasis", "prosody", "sub"]})

    def estimate_duration(self, text: str, words_per_minute: int) -> ProviderResult:
        words = len(re.findall(r"\b[\w'-]+\b", text))
        duration = round((words / max(words_per_minute, 1)) * 60, 2)
        return ProviderResult(self.provider_name, True, "Duration estimated from text only.", {"word_count": words, "estimated_duration_seconds": duration})


PROVIDERS = {
    "google_cloud_tts": MetadataOnlyProvider("google_cloud_tts", [{"voice_id": "en-GB-Neural2-B", "language": "en-GB"}]),
    "azure_speech": MetadataOnlyProvider("azure_speech", [{"voice_id": "en-GB-RyanNeural", "language": "en-GB"}]),
    "elevenlabs": MetadataOnlyProvider("elevenlabs", [{"voice_id": "insight-football-natural", "language": "en"}]),
    "openai_tts": MetadataOnlyProvider("openai_tts", [{"voice_id": "alloy", "language": "en"}]),
    "cartesia": MetadataOnlyProvider("cartesia", [{"voice_id": "sonic-english-natural", "language": "en"}]),
    "playht": MetadataOnlyProvider("playht", [{"voice_id": "en-football-conversational", "language": "en"}]),
}


def list_supported_providers() -> list[str]:
    return sorted(PROVIDERS)


def get_provider(provider_name: str) -> VoiceProvider:
    try:
        return PROVIDERS[provider_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported voice provider: {provider_name}") from exc
