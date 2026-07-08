from __future__ import annotations
import argparse, json
from pathlib import Path
from timeline_builder_engine.core import timeline_builder
from timeline_builder_engine.io import load_json
def main() -> int:
    p=argparse.ArgumentParser(description="Run Timeline Builder"); p.add_argument("--storyboard",required=True); p.add_argument("--visual-package",required=True); p.add_argument("--voice-package",required=True); p.add_argument("--asset-bundle",required=True); a=p.parse_args()
    r=timeline_builder(load_json(Path(a.storyboard)),load_json(Path(a.visual_package)),load_json(Path(a.voice_package)),load_json(Path(a.asset_bundle)))
    print(json.dumps({"success":True,"output":"editorial-brain/output/timeline.json","scenes":len(r["scenes"])},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
