# Urgent Patch: Production Requires Editor Selection

Date: 2026-07-09

## Policy

Production now requires a valid `editor_selection.json` before any workflow can run.

Defaults:

```json
{
  "production_requires_editor_selection": true,
  "allow_automatic_match_selection_in_production": false,
  "allow_match_selector_fallback": false
}
```

## Blocking Errors

Missing editor selection:

```json
{
  "code": "EDITOR_SELECTION_REQUIRED",
  "message": "No editor-selected match was provided. Production cannot continue. Please choose the match manually."
}
```

Automatic/system selection:

```json
{
  "code": "PRODUCTION_REQUIRES_HUMAN_EDITOR_SELECTION",
  "message": "Production requires selected_by to be human_editor."
}
```

## Verified Sample

Editor selection:

```text
Production: if-2026-07-09-france-morocco
Match: France vs Morocco
Competition: FIFA World Cup
Selected by: Human editor
Audio mode: silent
Render mode: creatomate
```

Creatomate payload check:

```text
Qarabag: false
Vestri: false
Liverpool: false
Arsenal: false
Premier League: false
```

## Tests

```text
Ran 411 tests
OK
```
