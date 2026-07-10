from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from app.config.settings import Settings
from app.models.output_models import AppError


class TelegramBot:
    def __init__(self, settings: Settings):
        self.settings = settings

    def configured(self) -> bool:
        return bool(self.settings.telegram_bot_token and self.settings.telegram_chat_id)

    def send_message(self, text: str) -> dict[str, object]:
        if not self.configured():
            raise AppError("TELEGRAM_DELIVERY_FAILED", "telegram", "Telegram is not configured.", False)
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        body = urllib.parse.urlencode({"chat_id": self.settings.telegram_chat_id, "text": text, "disable_web_page_preview": "true"}).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))

    def send_document(self, path: Path, caption: str) -> dict[str, object]:
        if not self.configured():
            raise AppError("TELEGRAM_DELIVERY_FAILED", "telegram", "Telegram is not configured.", False)
        boundary = "----InsightFootballBoundary"
        chunks: list[bytes] = []
        for name, value in {"chat_id": self.settings.telegram_chat_id, "caption": caption}.items():
            chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), str(value).encode(), b"\r\n"])
        chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="document"; filename="{path.name}"\r\n'.encode(), b"Content-Type: text/markdown\r\n\r\n", path.read_bytes(), b"\r\n", f"--{boundary}--\r\n".encode()])
        request = urllib.request.Request(f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendDocument", data=b"".join(chunks), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
