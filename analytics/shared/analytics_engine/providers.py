from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AnalyticsProvider(ABC):
    provider_name: str

    @abstractmethod
    def collect_metrics(self, published_package: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class YouTubeAnalyticsAdapter(AnalyticsProvider):
    provider_name = "youtube"

    def collect_metrics(self, published_package: dict[str, Any]) -> dict[str, Any]:
        return _metrics(self.provider_name, published_package, views=1240, watch_time=18200, comments=34, shares=18, ctr=5.8)


class FacebookInsightsAdapter(AnalyticsProvider):
    provider_name = "facebook"

    def collect_metrics(self, published_package: dict[str, Any]) -> dict[str, Any]:
        return _metrics(self.provider_name, published_package, views=860, watch_time=11900, comments=19, shares=26, ctr=4.2)


class TelegramStatisticsAdapter(AnalyticsProvider):
    provider_name = "telegram"

    def collect_metrics(self, published_package: dict[str, Any]) -> dict[str, Any]:
        return _metrics(self.provider_name, published_package, views=420, watch_time=5200, comments=11, shares=14, ctr=3.6)


def get_providers() -> list[AnalyticsProvider]:
    return [YouTubeAnalyticsAdapter(), FacebookInsightsAdapter(), TelegramStatisticsAdapter()]


def _metrics(platform: str, package: dict[str, Any], *, views: int, watch_time: int, comments: int, shares: int, ctr: float) -> dict[str, Any]:
    avg = round(watch_time / max(views, 1), 2)
    return {
        "platform": platform,
        "views": views,
        "watch_time_seconds": watch_time,
        "average_view_duration_seconds": avg,
        "audience_retention": [
            {"second": 0, "retention_percent": 100},
            {"second": 10, "retention_percent": 78},
            {"second": 20, "retention_percent": 61},
            {"second": 30, "retention_percent": 48},
            {"second": 42, "retention_percent": 31},
            {"second": 60, "retention_percent": 21},
        ],
        "ctr_percent": ctr,
        "likes": round(views * 0.043),
        "comments": comments,
        "shares": shares,
        "subscribers_gained": round(views * 0.006),
        "revenue": 0.0,
        "rpm": 0.0,
        "source": "mock_provider_dry_run" if package.get("dry_run", True) else "provider_adapter",
    }
