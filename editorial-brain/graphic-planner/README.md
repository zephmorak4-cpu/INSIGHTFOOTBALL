# Graphic Planner

Sprint 5 component 3. Reads `final-storyboard-package.json`, `asset_manifest.json`, and `asset_search_plan.json`, then writes:

- `graphic_requirements.json`
- `final-asset-package.json`

It plans cards, pitch diagrams, dashboard elements, captions, and CTA graphics. It does not render or generate final visuals.

```powershell
$env:PYTHONPATH='editorial-brain\graphic-planner\src'
python -m graphic_planner.cli --config editorial-brain\graphic-planner\config\graphic-planner.config.json --storyboard-package editorial-brain\output\final-storyboard-package.json --asset-manifest editorial-brain\output\asset_manifest.json --asset-search-plan editorial-brain\output\asset_search_plan.json
```

