import json
from pathlib import Path

from productpilot.agents.discovery_agent import process_request


def test_discovery_agent_returns_five_problem_statements():
    request_path = Path("productpilot/executions/discovery/company_request_template.json")
    with request_path.open("r", encoding="utf-8") as handle:
        request = json.load(handle)

    result = process_request(request)
    problem_statements = result["structured_output"].get("problem_statements", [])

    assert isinstance(problem_statements, list)
    assert len(problem_statements) == 5
    assert all(isinstance(item, str) and item.strip() for item in problem_statements)
