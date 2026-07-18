"""Run the discovery agent from the productpilot package."""

from __future__ import annotations

import json

from productpilot.agents.discovery_agent import process_request


if __name__ == "__main__":
    result = process_request()
    print(json.dumps(result, indent=2))
