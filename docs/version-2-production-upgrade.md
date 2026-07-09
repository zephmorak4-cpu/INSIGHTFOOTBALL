# INSIGHT FOOTBALL Version 2.0 Production Upgrade

Version 2.0 upgrades the existing production system. It does not replace the frozen architecture.

## Mandatory Production Changes

- Production runs cannot use example Daily Input files.
- Render production entrypoint builds `editorial-brain/output/live-daily-input.json` from the configured football API.
- Match Selector validates that production fixtures and the selected match belong to the production date.
- Viewer-facing text is checked for internal terminology and betting-style language.
- Visual plans require at least three visual elements per scene.
- The opening scene must include both club badges, competition logo, match title, modern scoreboard, and broadcast animation.
- Timeline scenes carry movement beats every 2 to 3 seconds.
- Captions are generated as short phrases, not paragraphs.
- Voice Director exposes human recorded narration, voice clone, and fallback AI voice modes. Human recorded narration is default.
- Final QC adds V2 editorial checks before approval.

## Live Fixture Environment

Production requires one of:

- `APP_FOOTBALL_API_KEY`
- `API_FOOTBALL_API_KEY`

Optional:

- `FOOTBALL_API_BASE_URL`
- `INSIGHT_FOOTBALL_FIXTURES_FILE` for controlled non-production fixture injection

The default API shape is API-FOOTBALL compatible: `response[].fixture`, `response[].league`, and `response[].teams`.

## Voice Pipeline

The V2 voice pipeline is represented by:

- `voice-input`
- `voice-processing`
- `voice-cleaning`
- `speech-alignment`
- `voice-sync`

Supported human narration formats are `wav`, `mp3`, and `m4a`.

## Migration Notes

- Keep example Daily Input files for tests only.
- Do not hardcode Liverpool vs Arsenal into production.
- Do not expose terms such as `X-Factor`, `Tactical Edge`, `Form Index`, or internal agent names to viewers.
- Prefer natural football language and narration-first storytelling.
- Rendered approval videos may use 720x1280 for memory-safe 9:16 approval previews on small Render cron plans.
