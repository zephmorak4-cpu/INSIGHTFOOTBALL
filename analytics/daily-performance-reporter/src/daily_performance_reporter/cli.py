from __future__ import annotations
import json
from analytics_engine.core import run_all
def main() -> int:
    result = run_all()
    package = result["learning_package"]
    print(json.dumps({"success": True, "output": "editorial-brain/output/learning-package.json", "recommendations": len(package["recommendations"]["recommendations"])}, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
