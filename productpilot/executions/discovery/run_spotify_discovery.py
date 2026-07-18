"""Run the discovery agent with a company/product-agnostic request payload."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from productpilot.agents.discovery_agent import process_request


if __name__ == "__main__":
    request_path = Path(__file__).with_name("spotify_request.json")
    with request_path.open("r", encoding="utf-8") as handle:
        request = json.load(handle)

    result = process_request(request)
    output_path = request_path.with_suffix(".output.json")
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    print(json.dumps({
        "company": request.get("tenant_id", "unknown"),
        "goal": request.get("user_intent", {}).get("goal"),
        "structured_output": result["structured_output"],
    }, indent=2))
