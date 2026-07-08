# Scriptwriter

The Scriptwriter is Sprint 3 component 1. It receives an approved `production_brief.json` and creates:

- `script-output-<production_id>.json`
- `voiceover-<production_id>.txt`

It preserves locked editorial fields, uses only claims from the brief, enforces the 120-145 word range, rejects betting and robotic language, and keeps the voiceover under 60 seconds.

## Sample

```powershell
$env:PYTHONPATH='editorial-brain\scriptwriter\src'
python -m scriptwriter.cli --config editorial-brain\scriptwriter\config\scriptwriter.config.json --brief editorial-brain\output\production-brief-if-2026-07-06-liverpool-arsenal.json
```

