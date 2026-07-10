from __future__ import annotations

from app.config.settings import Settings


class OpenAIService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def configured(self) -> bool:
        return bool(self.settings.openai_api_key)
