from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    success: bool
    message: str
    payload: dict


class VoiceProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate_voice(self, ssml: str, voice_id: str, output_path: str) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def list_voices(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def validate_ssml(self, ssml: str) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def estimate_duration(self, text: str, words_per_minute: int) -> ProviderResult:
        raise NotImplementedError
