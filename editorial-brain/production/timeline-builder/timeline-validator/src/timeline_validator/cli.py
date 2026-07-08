from __future__ import annotations
import json
from timeline_builder_engine.core import run_all
def main() -> int:
    r=run_all(); pkg=r["renderer_ready_package"]
    print(json.dumps({"success":True,"output":"editorial-brain/output/renderer-ready-package.json","render_readiness_status":pkg["render_readiness_status"],"duration":pkg["timeline"]["total_duration_seconds"]},indent=2)); return 0 if pkg["approval_status"]=="approved" else 1
if __name__=="__main__": raise SystemExit(main())
