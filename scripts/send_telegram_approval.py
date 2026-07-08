from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "editorial-brain" / "output"


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_message(run_url: str) -> str:
    daily = load_json(OUTPUT / "daily-run-report.json")
    readiness = load_json(OUTPUT / "publish_readiness_report.json")
    publishing = load_json(OUTPUT / "publishing_report.json")
    package = load_json(OUTPUT / "publish-ready-package.json")

    production_id = package.get("production_id") or readiness.get("production_id") or "unknown-production"
    match = package.get("match", {})
    match_name = f"{match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}"
    warnings = readiness.get("warnings") or publishing.get("warnings") or []
    warning_text = "\n".join(f"- {warning}" for warning in warnings[:6]) if warnings else "- None"

    return "\n".join(
        [
            "INSIGHT FOOTBALL APPROVAL REQUEST",
            "",
            f"Production: {production_id}",
            f"Match: {match_name}",
            f"Daily run: {'passed' if daily.get('success') else 'failed'}",
            f"Publish readiness: {readiness.get('final_status', 'unknown')}",
            f"Readiness score: {readiness.get('overall_score', 'unknown')}",
            f"Publishing mode: {'dry-run' if publishing.get('dry_run', True) else 'live'}",
            "",
            "Warnings:",
            warning_text,
            "",
            "Approval gate:",
            "Review the GitHub Actions artifacts and approve manually before any production publishing workflow is run.",
            "",
            f"Run: {run_url}" if run_url else "Run: unavailable",
        ]
    )


def send_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Send INSIGHT FOOTBALL approval request to Telegram.")
    parser.add_argument("--run-url", default=os.environ.get("GITHUB_RUN_URL", ""))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_APPROVAL_CHAT_ID") or os.environ.get("TELEGRAM_CHANNEL_ID", "")
    message = build_message(args.run_url)

    if args.dry_run or not token or not chat_id:
        print(json.dumps({"sent": False, "reason": "dry_run_or_missing_telegram_secrets", "message": message}, indent=2))
        return 0

    send_message(token, chat_id, message)
    print(json.dumps({"sent": True, "chat_id": chat_id}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

