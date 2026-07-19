"""Run the ProductPilot discovery workflow from the package entrypoint."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from productpilot.core.orchestrator import ProductPilotOrchestrator


if __name__ == "__main__":
    request_path = Path(__file__).with_name("company_request_template.json")
    with request_path.open("r", encoding="utf-8") as handle:
        request = json.load(handle)

    state = ProductPilotOrchestrator().run(request)
    output = {
        "workflow_id": request.get("workflow_id"),
        "problem": state.problem,
        "discovery_artifact": state.artifacts.get("discovery"),
        "kpi_tree_artifact": state.artifacts.get("kpi_tree"),
    }
    print(json.dumps(output, indent=2))
