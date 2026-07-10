from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.environ.get("APP_ENV", os.environ.get("INSIGHT_FOOTBALL_ENV", "development"))
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    openai_model: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    telegram_bot_token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_APPROVAL_CHAT_ID") or os.environ.get("TELEGRAM_CHANNEL_ID", "")
    football_api_key: str = os.environ.get("FOOTBALL_API_KEY") or os.environ.get("APP_FOOTBALL_API_KEY") or os.environ.get("API_FOOTBALL_API_KEY", "")
    football_api_base_url: str = os.environ.get("FOOTBALL_API_BASE_URL", "https://v3.football.api-sports.io")
    news_api_key: str = os.environ.get("NEWS_API_KEY", "")
    gnews_api_key: str = os.environ.get("GNEWS_API_KEY", "")
    weather_api_key: str = os.environ.get("WEATHER_API_KEY", "")
    data_dir: str = os.environ.get("DATA_DIR", "data")

    @property
    def production(self) -> bool:
        return self.app_env.lower() == "production"


def load_settings() -> Settings:
    return Settings()
