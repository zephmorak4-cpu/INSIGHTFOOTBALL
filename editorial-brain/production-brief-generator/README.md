# Production Brief Generator

Sprint 2 Component: `S2-C02`

The Production Brief Generator converts an approved validated Editorial Package into a clean brief for the future Scriptwriter. It does not write scripts, scenes, visuals, or render instructions.

## Input

```text
validated-editorial-package-<production_id>.json
```

## Output

```text
production-brief-<production_id>.json
```

## CLI

```text
$env:PYTHONPATH='editorial-brain/production-brief-generator/src'
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m production_brief_generator.cli --config editorial-brain/production-brief-generator/config/production-brief-generator.config.json --validated-package editorial-brain/output/validated-editorial-package-if-2026-07-06-liverpool-arsenal.json
```

## Rules

- Rejected packages cannot produce a brief.
- Locked fields must be preserved.
- Brand opening must be included.
- Forbidden betting phrases must be included.
- CTA direction must be included.
- Next agent must be `IF-A05`.
