"""Run the discovery agent and then the KPI Tree agent on the same input."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from productpilot.agents.discovery_agent import process_request
from productpilot.agents.kpi_tree_agent import KpiTreeAgent


if __name__ == "__main__":
    request_path = Path(__file__).resolve().parents[1] / "discovery" / "company_request_template.json"
    with request_path.open("r", encoding="utf-8") as handle:
        request = json.load(handle)

    discovery_result = process_request(request)
    kpi_result = KpiTreeAgent().run(discovery_result)
    output_path = Path(__file__).with_suffix(".output.json")
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(kpi_result, handle, indent=2)

    print(json.dumps(kpi_result["structured_output"], indent=2))
