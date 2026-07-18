import json
import unittest
from pathlib import Path

from productpilot.agents.discovery_agent import process_request
from productpilot.agents.kpi_tree_agent import KpiTreeAgent


class KpiTreeAgentTest(unittest.TestCase):
    def test_kpi_tree_agent_builds_tree_from_discovery_output(self):
        request_path = Path("productpilot/executions/discovery/company_request_template.json")
        with request_path.open("r", encoding="utf-8") as handle:
            request = json.load(handle)

        discovery_result = process_request(request)
        kpi_result = KpiTreeAgent().run(discovery_result)

        self.assertEqual(kpi_result["stage_id"], "kpi_tree")
        self.assertIn("structured_output", kpi_result)
        self.assertIn("kpi_tree", kpi_result["structured_output"])
        self.assertGreaterEqual(len(kpi_result["structured_output"]["kpi_tree"]), 3)


if __name__ == "__main__":
    unittest.main()
