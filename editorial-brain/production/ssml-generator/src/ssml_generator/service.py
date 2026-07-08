from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import SSMLGeneratorConfig
from .json_utils import load_json_file, write_json_file, write_text_file
from .logging_utils import StructuredLogger
from .validation import SSMLGeneratorValidator


class SSMLGeneratorService:
    def __init__(self, config: SSMLGeneratorConfig):
        self.config = config
        self.validator = SSMLGeneratorValidator()

    def run_from_files(self, script_package_path: Path, voice_plan_path: Path, pronunciation_dictionary_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(script_package_path), load_json_file(voice_plan_path), load_json_file(pronunciation_dictionary_path))

    def run(self, script_package: dict[str, Any], voice_plan: dict[str, Any], pronunciation_dictionary: dict[str, Any]) -> dict[str, Any]:
        production_id = script_package.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"ssml-generator-{production_id}")
        issues = self.validator.validate_inputs(script_package, voice_plan, pronunciation_dictionary)
        ssml, sentence_count = _build_ssml(voice_plan, pronunciation_dictionary, self.config)
        metadata = {
            "production_id": production_id,
            "component_id": self.config.component_id,
            "component_name": self.config.component_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": self.config.provider,
            "source_voice_plan": voice_plan.get("production_id", ""),
            "source_pronunciation_dictionary": pronunciation_dictionary.get("production_id", ""),
            "sentence_count": sentence_count,
            "supported_tags_used": ["speak", "p", "s", "break", "emphasis", "prosody", "sub"],
            "approval_status": "approved",
            "next_component": self.config.next_component,
        }
        issues.extend(self.validator.validate_ssml(ssml))
        issues.extend(self.validator.validate_metadata(metadata))
        if issues:
            logger.log({"event": "ssml_generation_failed", "issues": issues})
            return {"success": False, "error": {"code": "SSML_GENERATION_FAILED", "issues": issues}, "ssml": ssml, "ssml_metadata": metadata}
        ssml_path = self.config.output_directory / "voice.ssml"
        metadata_path = self.config.output_directory / "ssml_metadata.json"
        write_text_file(ssml_path, ssml)
        write_json_file(metadata_path, metadata)
        logger.log({"event": "ssml_written", "ssml_path": str(ssml_path), "metadata_path": str(metadata_path)})
        return {"success": True, "ssml": ssml, "ssml_metadata": metadata, "ssml_path": str(ssml_path), "ssml_metadata_path": str(metadata_path)}


def _build_ssml(voice_plan: dict[str, Any], dictionary: dict[str, Any], config: SSMLGeneratorConfig) -> tuple[str, int]:
    pronunciation = {item["term"].lower(): item for item in dictionary.get("items", [])}
    paragraphs = []
    sentence_count = 0
    for section in voice_plan.get("sections", []):
        rate = _rate(section["pace"])
        pitch = "+0st" if section["pitch"] == "medium" else section["pitch"]
        before = int(float(section["pause_before"]) * 1000) or config.pause_rules["section"]
        after = int(float(section["pause_after"]) * 1000) or config.pause_rules["sentence"]
        sentences = _sentences(section["narration_text"])
        sentence_count += len(sentences)
        rendered = [f'<break time="{before}ms"/>']
        for sentence in sentences:
            sentence_text = _apply_pronunciation(sentence, pronunciation)
            sentence_text = _apply_emphasis(sentence_text, section.get("emphasis_words", []))
            rendered.append(f'<s><prosody rate="{rate}" pitch="{pitch}" volume="medium">{sentence_text}</prosody></s>')
            rendered.append(f'<break time="{config.pause_rules["sentence"]}ms"/>')
        rendered.append(f'<break time="{after}ms"/>')
        paragraphs.append("<p>" + "".join(rendered) + "</p>")
    return "<speak>" + "".join(paragraphs) + "</speak>", sentence_count


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _rate(pace: str) -> str:
    return {"slightly_slow": "92%", "measured": "96%", "warm_prompt": "98%", "natural": "100%"}.get(pace, "100%")


def _apply_pronunciation(sentence: str, pronunciation: dict[str, dict[str, str]]) -> str:
    escaped = html.escape(sentence)
    for term, item in sorted(pronunciation.items(), key=lambda pair: len(pair[0]), reverse=True):
        escaped = re.sub(rf"\b{re.escape(html.escape(item['term']))}\b", f'<sub alias="{html.escape(item["phonetic"])}">{html.escape(item["term"])}</sub>', escaped, flags=re.IGNORECASE)
    return escaped


def _apply_emphasis(sentence: str, terms: list[str]) -> str:
    for term in sorted([term for term in terms if term], key=len, reverse=True):
        sentence = re.sub(rf"({re.escape(html.escape(term))})", r'<emphasis level="moderate">\1</emphasis>', sentence, flags=re.IGNORECASE)
    return sentence
