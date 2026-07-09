# INSIGHT FOOTBALL Version 2.0 Implementation Report

Date: 2026-07-09

## Summary

Version 2.0 upgrades the existing production system without rebuilding the frozen architecture. The upgrade enforces live match input in production, removes internal newsroom terminology from viewer-facing output, strengthens visual storytelling rules, adds narration workflow support, and extends final quality control.

## Implemented

- Production daily runs now build Daily Input from a live football fixture API when running in production mode.
- Production mode rejects example Daily Input files unless explicitly allowed.
- Match Selector validates that production fixtures and selected matches are for the production date.
- Script, storyboard, voice, timeline, captions, and final QC now protect viewer-facing surfaces from internal terms such as `X-Factor`, `Tactical Edge`, `Form Index`, and `Risk Meter`.
- Visual Director requires at least three visual elements per scene and club identity in the opening.
- Motion Planner and Timeline Builder enforce movement every 2-3 seconds.
- Rendering Engine adds broadcast-style opening identity, live score bar, and ticker elements.
- Voice Director now supports human-recorded narration as the default, plus voice clone and AI fallback modes.
- Voice Pipeline module added for input validation, processing, cleaning, speech alignment, and timeline sync.
- Final QC now validates V2 editorial, visual, motion, narration, and brand-safety rules.

## Verification

Command:

```powershell
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\run_tests.py
```

Result:

```text
Ran 396 tests
OK
```

## Deployment Notes

- `INSIGHT_FOOTBALL_ENV=production` is required for production enforcement.
- `APP_FOOTBALL_API_KEY` or `API_FOOTBALL_API_KEY` is required for live fixture selection.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_APPROVAL_CHAT_ID` are required for approval delivery.
- `INSIGHT_FOOTBALL_ALLOW_SAMPLE_DAILY_INPUT=true` is only for controlled tests and must not be used for daily production.
