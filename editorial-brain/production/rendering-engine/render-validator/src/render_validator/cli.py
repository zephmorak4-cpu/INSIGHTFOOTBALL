from __future__ import annotations
import argparse, json
from rendering_engine.core import run_all
def main() -> int:
    p=argparse.ArgumentParser(description="Run Rendering Engine"); p.add_argument("--renderer-profile",default="placeholder"); p.add_argument("--live",action="store_true"); a=p.parse_args()
    r=run_all(renderer_profile=a.renderer_profile,dry_run=not a.live); pkg=r["render_complete_package"]
    print(json.dumps({"success":True,"output":"editorial-brain/output/render-complete-package.json","renderer_profile":pkg["renderer_profile"],"approval_status":pkg["approval_status"],"final_video_path":pkg["final_video_path"]},indent=2)); return 0 if pkg["approval_status"]=="approved" else 1
if __name__=="__main__": raise SystemExit(main())
