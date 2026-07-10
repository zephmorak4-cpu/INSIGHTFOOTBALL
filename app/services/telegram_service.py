from __future__ import annotations

from pathlib import Path

from app.config.settings import Settings
from app.telegram.bot import TelegramBot


class TelegramService:
    def __init__(self, settings: Settings):
        self.bot = TelegramBot(settings)

    def send_message(self, text: str) -> dict[str, object]:
        return self.bot.send_message(text)

    def send_document(self, path: Path, caption: str) -> dict[str, object]:
        return self.bot.send_document(path, caption)
