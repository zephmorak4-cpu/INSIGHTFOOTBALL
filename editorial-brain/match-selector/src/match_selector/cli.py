"""Command-line entrypoint for Match Selector sample execution."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .json_utils import load_json_file, write_json_file
from .llm import OpenAICompatibleHTTPClient, RuleBasedMatchSelectorClient
from .service import MatchSelectorService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run INSIGHT FOOTBALL Match Selector")
    parser.add_argument("--input", required=True, help="Path to Daily Input JSON")
    parser.add_argument("--config", required=True, help="Path to Match Selector config JSON")
    parser.add_argument("--output", required=False, help="Optional output JSON path")
    parser.add_argument(
        "--provider",
        choices=["configured", "deterministic"],
        default="configured",
        help="Use configured LLM provider or deterministic local adapter",
    )
    args = parser.parse_args()

    config = load_config(Path(args.config))
    daily_input = load_json_file(Path(args.input))
    if args.provider == "deterministic" or config.provider == "deterministic":
        client = RuleBasedMatchSelectorClient(daily_input)
    else:
        client = OpenAICompatibleHTTPClient(
            endpoint=config.endpoint,
            model=config.model,
            api_key_env=config.api_key_env,
            timeout_seconds=config.timeout_seconds,
        )

    result = MatchSelectorService(config, client).run(daily_input)
    if args.output:
        write_json_file(Path(args.output), result)
    else:
        import json

        print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result.get("success", True) is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
