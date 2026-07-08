from __future__ import annotations

from typing import Any


class DashboardComposerValidator:
    def __init__(self, allowed_card_types: list[str]):
        self.allowed_card_types = set(allowed_card_types)

    def validate_inputs(self, storyboard: dict[str, Any], visual: dict[str, Any], camera: dict[str, Any], motion: dict[str, Any], captions: dict[str, Any]) -> list[str]:
        issues = []
        production_id = storyboard.get("production_id")
        for name, payload in [("visual", visual), ("camera", camera), ("motion", motion), ("captions", captions)]:
            if payload.get("production_id") != production_id:
                issues.append(f"{name}.production_id: must match storyboard")
        return issues

    def validate_dashboard(self, dashboard_plan: dict[str, Any]) -> list[str]:
        issues = []
        found = {card.get("card_type") for card in dashboard_plan.get("dashboard_cards", [])}
        for card_type in self.allowed_card_types:
            if card_type not in found:
                issues.append(f"dashboard missing card: {card_type}")
        for card in dashboard_plan.get("dashboard_cards", []):
            if not card.get("icon"):
                issues.append(f"{card.get('card_type')}: icon required")
            if card.get("display_time", 0) <= 0:
                issues.append(f"{card.get('card_type')}: display_time must be positive")
        return issues

    @staticmethod
    def validate_final_package(package: dict[str, Any]) -> list[str]:
        if not package.get("validation_report", {}).get("all_scenes_covered"):
            return ["validation_report.all_scenes_covered: must be true"]
        return []
