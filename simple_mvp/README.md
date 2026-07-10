# INSIGHT FOOTBALL Simple MVP

This is the active production flow.

The legacy multi-agent pipeline remains in the repository, but production must not call it.

## Flow

```text
manual_match_input.json
  -> match_data_fetcher.py
  -> ai_editor.py
  -> asset_resolver.py
  -> creatomate_renderer.py
  -> telegram_delivery.py
  -> qc.py
```

## Run

```powershell
python -m simple_mvp.run_production --input simple_mvp/manual_match_input.json
```

The production entrypoint delegates to the same command:

```powershell
python scripts/render_daily_entrypoint.py
```

## Required Input

`manual_match_input.json` must be written by a human editor. Automatic selection is blocked.

```json
{
  "production_id": "if-2026-07-10-spain-belgium",
  "match": "Spain vs Belgium",
  "home_team": "Spain",
  "away_team": "Belgium",
  "competition": "FIFA World Cup",
  "stage": "Quarter-final",
  "kickoff_time": "2026-07-10T20:00:00+01:00",
  "selected_by": "human_editor",
  "audio_mode": "silent_capcut"
}
```

## Required Environment

```text
APP_FOOTBALL_API_KEY
GNEWS_API_KEY
OPENAI_API_KEY
CREATOMATE_API_KEY
CREATOMATE_MASTER_TEMPLATE_ID
INSIGHT_FOOTBALL_LOGO_URL
TELEGRAM_BOT_TOKEN
TELEGRAM_APPROVAL_CHAT_ID
```

## Outputs

```text
simple_mvp/output/match_data.json
simple_mvp/output/content_package.json
simple_mvp/output/resolved_assets.json
simple_mvp/output/creatomate_render_payload.json
simple_mvp/output/creatomate_render_response.json
simple_mvp/output/render_status.json
simple_mvp/output/render_result.json
simple_mvp/output/telegram_delivery_report.json
simple_mvp/output/mvp_production_report.json
renders/{production_id}/final_video.mp4
renders/{production_id}/narration_script.txt
```

## Stop Conditions

The MVP stops instead of guessing when:

- the manual input file is missing
- `selected_by` is not `human_editor`
- real match data is insufficient
- the AI script is generic or uses sample leakage
- the master Creatomate template ID is missing
- the INSIGHT FOOTBALL logo URL is missing
- the MP4 does not exist
- Telegram delivery fails

## QC Status

The only allowed QC statuses are:

```text
PASS
FAIL
NEEDS_HUMAN_REVIEW
```
