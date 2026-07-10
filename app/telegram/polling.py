from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from app.config.settings import load_settings
from app.main import process_text
from app.telegram.bot import TelegramBot
from app.telegram.handlers import command_response
from app.telegram.message_parser import FORMAT_HINT


def _api(token: str, method: str, params: dict[str, object]) -> dict[str, object]:
    body = urllib.parse.urlencode(params).encode("utf-8")
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=body, method="POST")
    with urllib.request.urlopen(request, timeout=35) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def main() -> int:
    settings = load_settings()
    if not settings.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is not configured.")
        return 1
    bot = TelegramBot(settings)
    offset = 0
    print("INSIGHT FOOTBALL Telegram polling started.")
    while True:
        data = _api(settings.telegram_bot_token, "getUpdates", {"offset": offset, "timeout": 25})
        for update in data.get("result", []):
            offset = max(offset, int(update.get("update_id", 0)) + 1)
            message = update.get("message", {})
            text = str(message.get("text", "")).strip()
            if not text:
                continue
            chat_id = str(message.get("chat", {}).get("id", ""))
            original_chat = settings.telegram_chat_id
            object.__setattr__(settings, "telegram_chat_id", chat_id or original_chat)
            if text.startswith("/"):
                bot.send_message(command_response(text, settings))
                continue
            bot.send_message(f"Researching {text.splitlines()[0]}...")
            result = process_text(text, send_telegram=True)
            if not result.get("success"):
                bot.send_message(result.get("error", {}).get("message", FORMAT_HINT))
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
