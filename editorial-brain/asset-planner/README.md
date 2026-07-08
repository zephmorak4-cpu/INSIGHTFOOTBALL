# Asset Planner

Sprint 5 component 1. Reads `final-storyboard-package.json` and writes `asset_manifest.json`.

It identifies required, optional, and reusable assets; maps assets to scenes; lists missing/review assets; and surfaces legal warnings. It does not download or generate assets.

```powershell
$env:PYTHONPATH='editorial-brain\asset-planner\src'
python -m asset_planner.cli --config editorial-brain\asset-planner\config\asset-planner.config.json --storyboard-package editorial-brain\output\final-storyboard-package.json
```

