# INSIGHT FOOTBALL

INSIGHT FOOTBALL is an AI-assisted football media production system for short-form match insight videos.

The repository contains the frozen architecture, production blueprints, editorial agents, visual planning modules, publishing dry-run engine, analytics engine, schemas, prompts, tests, and sample Liverpool vs Arsenal production artifacts.

## Current Production Status

The codebase is Version 2.0 production-baseline ready and defaults to safe dry-run behavior.

- Editorial Brain: implemented.
- Script, storyboard, voice, asset, timeline, render, QC, distribution, and analytics modules: implemented as sprint modules.
- Production Match Selector: live fixture enforced. Example matches are tests only.
- Visual production: V2 broadcast rules enforce club identity, motion beats, captions, and non-text-only scenes.
- Voice pipeline: human recorded narration is the default mode, with voice clone and fallback AI voice support.
- Publishing: dry-run by default.
- Live platform upload: disabled until credentials, real media assets, and human approval are present.
- MP4 rendering: FFmpeg adapter supports real 9:16 approval videos with branded opening, watermark, transitions, and end card.

## Repository Layout

```text
analytics/              Analytics and learning engine.
blueprints/             Frozen architecture and communication standards.
daily_packages/         Sample daily input packages.
distribution/           Publishing engine and platform payload adapters.
editorial-brain/        Editorial, creative, production, rendering, and QC modules.
prompts/                Prompt library extracts.
renders/                Sample render artifacts.
schemas/                Top-level production package schema.
templates/              Daily input and operating templates.
scripts/                Local and CI utility scripts.
```

## Requirements

- Python 3.12 or newer.
- Python packages listed in `requirements.txt`.
- Live LLM, analytics, rendering, and publishing integrations require environment variables listed in `.env.example`.
- Production live match selection requires `APP_FOOTBALL_API_KEY` or `API_FOOTBALL_API_KEY`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run Tests

```bash
python scripts/run_tests.py
```

The full regression suite currently covers editorial, production, publishing, and analytics modules.

## Version 2.0 Production Rules

- Production runs must not use `editorial-brain/examples/*` Daily Input files.
- `scripts/render_daily_entrypoint.py` builds a live Daily Input from today's football API fixtures when `INSIGHT_FOOTBALL_ENV=production`.
- Viewer-facing output must not contain internal terms such as `X-Factor`, `Tactical Edge`, `Story Hunter`, or `Editorial Brain`.
- Every scene must include at least three visual elements and movement every 2 to 3 seconds.
- Opening five seconds must show both club identities, competition identity, match title, scoreboard, and broadcast animation.

See [docs/version-2-production-upgrade.md](docs/version-2-production-upgrade.md).

## Readiness Check

Run:

```bash
python scripts/readiness_check.py
```

This checks the local runtime, Render configuration, workflow files, and whether required Telegram environment variables are present locally. It never prints secret values.

## Sample Editorial Run

From the repository root:

```powershell
$env:PYTHONPATH='editorial-brain/editorial-orchestrator/src'
python -m editorial_orchestrator.cli --config editorial-brain/editorial-orchestrator/config/editorial-orchestrator.config.json --daily-input editorial-brain/examples/liverpool-arsenal-daily-input.json
```

Expected outputs include:

```text
editorial-brain/output/editorial-package-if-2026-07-06-liverpool-arsenal.json
editorial-brain/output/execution-report-if-2026-07-06-liverpool-arsenal.json
```

## Publishing Dry Run

Publishing is safe by default and does not upload to platforms unless live mode is explicitly enabled and credentials are present.

```powershell
$env:PYTHONPATH='distribution/publishing-engine/shared;distribution/publishing-engine/publishing-report-generator/src'
python -m publishing_report_generator.cli
```

Live publishing should only be enabled after:

- A real `.mp4` render exists.
- All fact-check and manual-review warnings are resolved.
- Platform credentials are configured as secrets.
- Human approval has been recorded.

## Daily Production Run

GitHub Actions contains a scheduled dry-run workflow:

```text
.github/workflows/daily-production.yml
```

It runs every day at:

```text
10:00 Africa/Lagos
09:00 UTC
```

The daily workflow:

- Runs the full regression test suite.
- Runs the daily dry-run production script.
- Refreshes the render package before Final QC.
- Generates the approval package.
- Keeps platform publishing in dry-run mode.
- Sends a Telegram approval request when Telegram approval secrets are configured.
- Attaches `final_video.mp4` when a real MP4 render exists.
- Uploads approval artifacts to the GitHub Actions run.

Manual execution is also available from GitHub Actions using `workflow_dispatch`.

Required approval secrets:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_APPROVAL_CHAT_ID
```

Use `TELEGRAM_APPROVAL_CHAT_ID` for the private approval chat, group, or channel that receives review requests. Keep it separate from `TELEGRAM_CHANNEL_ID`, which is reserved for the eventual public publishing destination.

## Render Deployment

Render deployment is defined in:

```text
render.yaml
```

It provisions a Render cron service that runs at:

```text
10:00 Africa/Lagos
09:00 UTC
```

The Render entrypoint is:

```text
python scripts/render_daily_entrypoint.py
```

The cron job runs tests, runs the daily dry-run production flow, and sends a Telegram approval request when secrets are configured. It does not live-publish.

Render setup details are in:

```text
docs/render-deployment.md
```

## Real MP4 Rendering

The FFmpeg renderer can generate a real 9:16 `final_video.mp4` from:

```text
editorial-brain/output/renderer-ready-package.json
```

It applies the mandatory INSIGHT FOOTBALL brand standard:

- 1.5-second opening sting.
- Persistent corner logo.
- 0.3-second section transition stings.
- Branded panels and lower thirds.
- 4-second end card.

The renderer requires `ffmpeg` on PATH or:

```text
FFMPEG_BINARY_PATH=/path/to/ffmpeg
```

If FFmpeg is unavailable, real rendering fails clearly and no publishable MP4 is produced.

Render installs FFmpeg via:

```text
Aptfile
```

## Telegram Approval With Video

The Telegram approval sender checks the production artifacts for a real MP4:

```text
publish-ready-package.final_video_path
render-complete-package.final_video_path
render_artifacts.final_video_path
```

If the path exists and ends in `.mp4`, Telegram receives the video via `sendVideo` plus the full approval context as a follow-up message. Placeholder JSON renders are ignored and the approval falls back to text-only.

Set the daily renderer with:

```text
INSIGHT_FOOTBALL_RENDERER_PROFILE=ffmpeg
```

Use `placeholder` only for safe contract runs where no MP4 is expected.

## Human Approval Gate

Production publishing is separated from daily package generation.

```text
.github/workflows/approved-production-publish.yml
```

This workflow only runs manually. It requires:

```text
approval_statement=APPROVED
```

By default, this workflow still runs publishing in dry-run mode. Set `live_publish=true` only after:

- The approval package has been reviewed.
- The render is a real platform-ready video.
- All required secrets are configured.
- The publish-ready package has no blocking issues.
- Human approval has been explicitly given.

The approved workflow currently targets Telegram only, so missing YouTube or Facebook credentials cannot block the first live Telegram release.

## Live Telegram Publishing

After human approval, the manual workflow can publish the approved MP4 to the public Telegram channel.

Required secrets:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHANNEL_ID
```

Required runtime conditions:

- `approval_statement=APPROVED`
- `live_publish=true`
- `HUMAN_APPROVAL_CONFIRMED=true` set by the workflow
- `publish-ready-package.final_video_path` points to a real `.mp4`

The Telegram publisher uses `sendVideo`. Placeholder JSON renders are blocked and cannot be live-published.

## Analytics Run

```powershell
$env:PYTHONPATH='analytics/shared;analytics/daily-performance-reporter/src'
python -m daily_performance_reporter.cli
```

This writes the learning package to:

```text
editorial-brain/output/learning-package.json
```

## Environment Variables

Copy `.env.example` for local use and fill values outside Git.

```text
.env
```

Never commit real API keys, bot tokens, OAuth credentials, channel IDs, or access tokens.

## Security Notes

- Tokens pasted into chat or committed anywhere should be considered exposed.
- Rotate exposed credentials before production use.
- Keep live publishing disabled until real media, verified data, and review gates pass.
