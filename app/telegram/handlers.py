from __future__ import annotations

from app import APP_VERSION
from app.config.settings import Settings


def command_response(command: str, settings: Settings, last_successful_run: str | None = None) -> str:
    if command == "/start":
        return "Send a match like:\n\nChelsea vs Arsenal\nPremier League"
    if command == "/help":
        return "Format:\nTEAM A vs TEAM B\nCOMPETITION\n\nExample:\nChelsea vs Arsenal\nPremier League"
    if command == "/health":
        return "\n".join([
            "application status: ok",
            f"version: {APP_VERSION}",
            f"OpenAI configured: {'yes' if settings.openai_api_key else 'no'}",
            f"Telegram configured: {'yes' if settings.telegram_bot_token and settings.telegram_chat_id else 'no'}",
            f"football API configured: {'yes' if settings.football_api_key else 'no'}",
            f"last successful run: {last_successful_run or 'none'}",
        ])
    return "Unknown command. Send /help."
