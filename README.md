# INSIGHT FOOTBALL

INSIGHT FOOTBALL is an AI-assisted football media production system for short-form match insight videos.

The repository contains the frozen architecture, production blueprints, editorial agents, visual planning modules, publishing dry-run engine, analytics engine, schemas, prompts, tests, and sample Liverpool vs Arsenal production artifacts.

## Current Production Status

The codebase is production-baseline ready and defaults to safe dry-run behavior.

- Editorial Brain: implemented.
- Script, storyboard, voice, asset, timeline, render, QC, distribution, and analytics modules: implemented as sprint modules.
- Publishing: dry-run by default.
- Live platform upload: disabled until credentials, real media assets, and human approval are present.
- Current sample render: placeholder JSON, not an encoded video file.

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
- No required third-party Python packages for the current deterministic test suite.
- Live LLM, analytics, rendering, and publishing integrations require environment variables listed in `.env.example`.

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

