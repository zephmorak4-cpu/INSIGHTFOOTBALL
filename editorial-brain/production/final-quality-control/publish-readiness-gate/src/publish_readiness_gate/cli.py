from __future__ import annotations
import json
from final_quality_control.core import run_all
def main() -> int:
    result = run_all()
    report = result["publish_readiness_report"]
    print(json.dumps({"success": True, "output": "editorial-brain/output/publish-ready-package.json", "final_status": report["final_status"], "overall_score": report["overall_score"]}, indent=2))
    return 0 if report["approval_status"] in {"approved_for_publishing", "needs_human_review"} else 1
if __name__ == "__main__":
    raise SystemExit(main())
