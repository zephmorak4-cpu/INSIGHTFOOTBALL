from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IllustrationResult:
    success: bool
    provider: str
    file_path: str
    metadata: dict


class IllustrationProvider(ABC):
    provider_name: str

    @abstractmethod
    def create_placeholder(self, task: dict, output_root: Path) -> IllustrationResult:
        raise NotImplementedError


class StaticPlaceholderProvider(IllustrationProvider):
    provider_name = "static_placeholder"

    def create_placeholder(self, task: dict, output_root: Path) -> IllustrationResult:
        output_root.mkdir(parents=True, exist_ok=True)
        path = output_root / f"{task['asset_id']}.svg"
        title = _safe_text(task.get("asset_type", "asset").replace("_", " ").title())
        subtitle = _safe_text(task.get("asset_id", "placeholder"))
        color = "#16a34a" if "pitch" in subtitle else "#2563eb"
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">'
            '<rect width="1080" height="1920" fill="#101827"/>'
            f'<rect x="90" y="220" width="900" height="1480" rx="48" fill="{color}" opacity="0.16"/>'
            '<path d="M180 960 H900 M540 320 V1600" stroke="#f8fafc" stroke-width="10" opacity="0.25"/>'
            f'<text x="540" y="900" text-anchor="middle" font-family="Arial" font-size="64" fill="#f8fafc">{title}</text>'
            f'<text x="540" y="990" text-anchor="middle" font-family="Arial" font-size="38" fill="#cbd5e1">{subtitle}</text>'
            "</svg>"
        )
        path.write_text(svg, encoding="utf-8")
        return IllustrationResult(True, self.provider_name, str(path), {"legal_status": "approved_placeholder", "format": "svg", "dimensions": "1080x1920"})


def get_provider(name: str) -> IllustrationProvider:
    if name in {"placeholder", "static_placeholder", "local_svg_generator"}:
        return StaticPlaceholderProvider()
    raise ValueError(f"Unsupported illustration provider: {name}")


def _safe_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "").replace(">", "")
