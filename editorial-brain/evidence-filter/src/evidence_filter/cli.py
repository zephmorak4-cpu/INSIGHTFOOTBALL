"""Command-line entrypoint for Evidence Filter sample execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .json_utils import load_json_file, write_json_file
from .llm import OpenAICompatibleHTTPClient, RuleBasedEvidenceFilterClient
from .service import EvidenceFilterService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run INSIGHT FOOTBALL Evidence Filter")
    parser.add_argument("--daily-input", required=True, help="Path to Daily Input JSON")
    parser.add_argument("--match-selection", required=True, help="Path to approved Match Selection JSON")
    parser.add_argument("--story-hunter", required=True, help="Path to approved Story Hunter JSON")
    parser.add_argument("--config", required=True, help="Path to Evidence Filter config JSON")
    parser.add_argument("--output", required=False, help="Optional output JSON path")
    parser.add_argument(
        "--provider",
        choices=["configured", "deterministic"],
        default="configured",
        help="Use configured LLM provider or deterministic local adapter",
    )
    args = parser.parse_args()

    config = load_config(Path(args.config))
    daily_input = load_json_file(Path(args.daily_input))
    match_selection = load_json_file(Path(args.match_selection))
    story_hunter = load_json_file(Path(args.story_hunter))
    if args.provider == "deterministic" or config.provider == "deterministic":
        client = RuleBasedEvidenceFilterClient(daily_input, match_selection, story_hunter)
    else:
        client = OpenAICompatibleHTTPClient(
            endpoint=config.endpoint,
            model=config.model,
            api_key_env=config.api_key_env,
            timeout_seconds=config.timeout_seconds,
        )

    result = EvidenceFilterService(config, client).run(daily_input, match_selection, story_hunter)
    if args.output:
        write_json_file(Path(args.output), result)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result.get("success", True) is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
