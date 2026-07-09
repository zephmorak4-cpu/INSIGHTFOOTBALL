from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def gh_authenticated() -> bool:
    if not command_available("gh"):
        return False
    result = subprocess.run(["gh", "auth", "status"], cwd=ROOT, text=True, capture_output=True)
    return result.returncode == 0


def env_set(name: str) -> bool:
    return bool(os.environ.get(name))


def ffmpeg_ready() -> bool:
    configured = os.environ.get("FFMPEG_BINARY_PATH")
    return bool(configured and Path(configured).exists()) or command_available("ffmpeg")


def render_config_ready() -> bool:
    path = ROOT / "render.yaml"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "schedule: \"0 9 * * *\"" in text and "INSIGHT_FOOTBALL_RENDERER_PROFILE" in text and ("value: ffmpeg" in text or "value: creatomate" in text)


def main() -> int:
    checks = {
        "repo": {
            "render_yaml_exists": (ROOT / "render.yaml").exists(),
            "render_config_has_renderer_profile": render_config_ready(),
            "aptfile_installs_ffmpeg": (ROOT / "Aptfile").exists() and "ffmpeg" in (ROOT / "Aptfile").read_text(encoding="utf-8"),
            "daily_workflow_exists": (ROOT / ".github" / "workflows" / "daily-production.yml").exists(),
            "approval_workflow_exists": (ROOT / ".github" / "workflows" / "approved-production-publish.yml").exists(),
        },
        "local_runtime": {
            "ffmpeg_available": ffmpeg_ready(),
            "github_cli_authenticated": gh_authenticated(),
        },
        "telegram_env": {
            "TELEGRAM_BOT_TOKEN": env_set("TELEGRAM_BOT_TOKEN"),
            "TELEGRAM_APPROVAL_CHAT_ID": env_set("TELEGRAM_APPROVAL_CHAT_ID"),
            "TELEGRAM_CHANNEL_ID": env_set("TELEGRAM_CHANNEL_ID"),
        },
    }
    blocking = []
    if not checks["repo"]["render_config_has_renderer_profile"]:
        blocking.append("Render config does not define a production renderer profile.")
    if not checks["repo"]["aptfile_installs_ffmpeg"]:
        blocking.append("Aptfile does not install ffmpeg.")
    if not checks["local_runtime"]["ffmpeg_available"]:
        blocking.append("Local FFmpeg is unavailable. Render can still be ready if Aptfile is deployed.")
    if not checks["local_runtime"]["github_cli_authenticated"]:
        blocking.append("GitHub CLI is not authenticated locally; cannot trigger/inspect Actions from this machine.")
    for name, ok in checks["telegram_env"].items():
        if not ok:
            blocking.append(f"{name} is missing locally. Confirm it exists in Render/GitHub secrets.")
    report = {"ready_for_code_deploy": not blocking or all("locally" in issue or "Local" in issue or "GitHub CLI" in issue for issue in blocking), "checks": checks, "blocking_or_external_actions": blocking}
    print(json.dumps(report, indent=2))
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
