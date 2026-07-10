from __future__ import annotations

import argparse
import json
import sys

from app.config.logging_config import log_event
from app.config.settings import load_settings
from app.content.directors_sheet import build_directors_sheet, directors_filename
from app.content.output_validator import validate_outputs
from app.content.script_writer import write_script
from app.football.data_collector import collect_match_data
from app.football.data_normalizer import normalize_match_data
from app.football.data_validator import validate_data
from app.football.fixture_resolver import resolve_fixture
from app.intelligence.insight_discovery import discover_insight
from app.intelligence.probability_engine import calculate_probabilities
from app.intelligence.report_builder import build_report
from app.models.output_models import AppError
from app.storage.run_repository import RunRepository
from app.telegram.formatter import format_match_found, format_script
from app.telegram.handlers import command_response
from app.telegram.message_parser import parse_match_message
from app.telegram.bot import TelegramBot
from app.utils.ids import new_run_id


def process_text(text: str, *, send_telegram: bool = False) -> dict[str, object]:
    settings = load_settings()
    run_id = new_run_id()
    repo = RunRepository(settings.data_dir, run_id)
    try:
        if text.strip().startswith("/"):
            response = command_response(text.strip(), settings)
            repo.write_json("final_output.json", {"run_id": run_id, "command": text.strip(), "response": response})
            return {"success": True, "run_id": run_id, "response": response}
        request = parse_match_message(text, run_id)
        repo.write_json("request.json", request.__dict__)
        log_event(repo.run_dir, run_id=run_id, stage="message_parser", event="parsed", message="Input parsed.")
        fixture = resolve_fixture(request, settings, run_id)
        repo.write_json("fixture.json", fixture.__dict__)
        raw = collect_match_data(fixture, settings, run_id)
        repo.write_json("raw_data.json", {"fixture": fixture.__dict__, "categories": raw.categories, "sources": raw.sources})
        normalized = normalize_match_data(raw)
        repo.write_json("normalized_data.json", normalized)
        validation = validate_data(request, normalized)
        repo.write_json("validation.json", validation)
        report = build_report(normalized, validation)
        repo.write_text("intelligence_report.md", report)
        insight = discover_insight(normalized, report)
        repo.write_json("insight_discovery.json", insight)
        probabilities = calculate_probabilities(normalized, validation)
        repo.write_json("probabilities.json", probabilities)
        script = write_script(normalized["fixture"], insight, probabilities)
        repo.write_text("script.txt", script)
        sheet = build_directors_sheet(normalized["fixture"], script)
        sheet_path = repo.write_text(directors_filename(fixture.home_team, fixture.away_team), sheet)
        repo.write_text("directors_sheet.md", sheet)
        output_validation = validate_outputs(report, insight, probabilities, script, sheet)
        final = {"run_id": run_id, "fixture": fixture.__dict__, "validation": validation, "insight": insight, "probabilities": probabilities, "script": script, "directors_sheet_path": str(sheet_path), "output_validation": output_validation}
        repo.write_json("final_output.json", final)
        if send_telegram:
            bot = TelegramBot(settings)
            bot.send_message(format_match_found(fixture, run_id))
            bot.send_document(repo.run_dir / "intelligence_report.md", "FOOTBALL INTELLIGENCE REPORT")
            bot.send_message(format_script(script, probabilities, probabilities["model_confidence"]))
            bot.send_document(sheet_path, "DIRECTOR'S SHEET\nOpen this file while editing in CapCut.")
        return {"success": output_validation["status"] != "FAIL", **final}
    except AppError as exc:
        repo.append_error(json.dumps(exc.to_dict()))
        repo.write_json("final_output.json", {"success": False, "error": exc.to_dict()})
        return {"success": False, "error": exc.to_dict(), "run_id": run_id}


def main() -> int:
    parser = argparse.ArgumentParser(description="INSIGHT FOOTBALL clean MVP")
    parser.add_argument("--text", default="")
    parser.add_argument("--send-telegram", action="store_true")
    parser.add_argument("--health", action="store_true")
    args = parser.parse_args()
    if args.health:
        settings = load_settings()
        print(command_response("/health", settings))
        return 0
    if not args.text:
        print("Provide --text with a match request.")
        return 1
    result = process_text(args.text, send_telegram=args.send_telegram)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
