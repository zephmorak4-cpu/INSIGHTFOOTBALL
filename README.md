# INSIGHT FOOTBALL Clean MVP

INSIGHT FOOTBALL now produces football research and editing guidance only.

It does not render video, generate voice, publish automatically, or run the legacy multi-agent newsroom.

## Purpose

Input from Telegram:

```text
Chelsea vs Arsenal
Premier League
```

Output:

1. Football Intelligence Report
2. Insight Discovery
3. 60-second narration script
4. Director's Sheet for manual CapCut editing

## Architecture

```text
Telegram
-> Research
-> Intelligence
-> Script
-> Director's Sheet
```

Active project structure:

```text
app/
  config/
  telegram/
  football/
  intelligence/
  content/
  models/
  services/
  storage/
  utils/
tests/
scripts/
data/runs/
```

Legacy code remains archived/inactive and is not imported by production.

## Telegram Input

Supported formats:

```text
Chelsea vs Arsenal
Premier League
```

```text
Chelsea vs Arsenal | Premier League
```

```text
Match: Chelsea vs Arsenal
Competition: Premier League
```

Commands:

```text
/start
/help
/health
```

## Environment

Copy `.env.example` and set values in your runtime environment.

Required for production:

```text
OPENAI_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID or TELEGRAM_APPROVAL_CHAT_ID
FOOTBALL_API_KEY or APP_FOOTBALL_API_KEY
FOOTBALL_API_BASE_URL
GNEWS_API_KEY
APP_ENV=production
```

No secrets should be committed.

## Local Run

```powershell
python -m app.main --text "Chelsea vs Arsenal`nPremier League"
```

Send Telegram outputs:

```powershell
python -m app.main --text "Chelsea vs Arsenal`nPremier League" --send-telegram
```

Health:

```powershell
python scripts/health_check.py
```

Inspect a run:

```powershell
python scripts/inspect_run.py RUN_ID
```

## Production Startup

```powershell
python -m app.telegram.polling
```

Render runs this as a worker, not as a daily cron.

## Run Storage

Each run is saved under:

```text
data/runs/{run_id}/
```

Files include:

```text
request.json
fixture.json
raw_data.json
normalized_data.json
validation.json
intelligence_report.md
insight_discovery.json
probabilities.json
script.txt
directors_sheet.md
final_output.json
errors.log
```

## Tests

```powershell
python scripts/run_tests.py
```

Tests use mocked provider responses. Mock data is not used in production.

## Provider Notes

Current football source:

- API-Football: fixtures, teams, recent fixtures, head-to-head where available

Current news source:

- GNews: recent headlines

Unavailable fields are left unavailable. The app does not invent missing injuries, lineups, xG, formations, or player ratings when the provider does not return them.

## Content Safety

The script must:

- avoid betting instructions
- avoid guarantees
- avoid internal labels
- include both teams
- end with a relevant question
- keep probabilities as uncertainty, not certainty
