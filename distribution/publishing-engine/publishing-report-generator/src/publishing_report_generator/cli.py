from __future__ import annotations
import argparse, json
from publishing_engine.core import run_all
def main() -> int:
    p=argparse.ArgumentParser(description="Run Publishing Engine"); p.add_argument("--live", action="store_true"); p.add_argument("--platform", action="append", choices=["youtube","facebook","telegram"], help="Platform to publish. Repeat for multiple platforms. Defaults to all platforms."); args=p.parse_args()
    result=run_all(dry_run=not args.live, live=args.live, platforms=args.platform)
    report=result["publishing_report"]
    print(json.dumps({"success": True, "output": "editorial-brain/output/published-package.json", "final_status": report["final_status"], "dry_run": report["dry_run"]}, indent=2))
    return 0 if report["final_status"] in {"dry_run_complete", "published", "partially_published"} else 1
if __name__ == "__main__":
    raise SystemExit(main())
