# Search Planner

Sprint 5 component 2. Reads `asset_manifest.json` and writes `asset_search_plan.json`.

It creates search and preparation instructions only. It does not browse, download, scrape, or approve external media.

```powershell
$env:PYTHONPATH='editorial-brain\search-planner\src'
python -m search_planner.cli --config editorial-brain\search-planner\config\search-planner.config.json --asset-manifest editorial-brain\output\asset_manifest.json
```

