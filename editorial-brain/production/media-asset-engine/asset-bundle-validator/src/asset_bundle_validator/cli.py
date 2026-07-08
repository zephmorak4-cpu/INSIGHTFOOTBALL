from __future__ import annotations

import json

from media_asset_engine.core import run_all


def main() -> int:
    result = run_all()
    bundle = result["asset_bundle"]["media_asset_bundle"]
    print(json.dumps({"success": True, "output": "editorial-brain/output/media-asset-bundle.json", "render_readiness_status": bundle["render_readiness_status"]}, indent=2))
    return 0 if bundle["approval_status"] in {"approved", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
