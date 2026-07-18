import json
import unittest
from pathlib import Path

from productpilot.core.orchestrator import ProductPilotOrchestrator


class ProductPilotOrchestratorTests(unittest.TestCase):
    def test_orchestrator_runs_discovery_and_kpi_tree(self) -> None:
        request_path = Path("productpilot/executions/discovery/company_request_template.json")
        with request_path.open("r", encoding="utf-8") as handle:
            request = json.load(handle)

        orchestrator = ProductPilotOrchestrator()
        state = orchestrator.run(request)

        self.assertEqual(state.request["workflow_id"], request["workflow_id"])
        self.assertIn("discovery", state.artifacts)
        self.assertIn("kpi_tree", state.artifacts)
        self.assertEqual(state.artifacts["discovery"]["stage_id"], "discovery")
        self.assertEqual(state.artifacts["kpi_tree"]["stage_id"], "kpi_tree")
        self.assertEqual(state.artifacts["kpi_tree"]["structured_output"]["summary"].startswith("KPI tree built"), True)


if __name__ == "__main__":
    unittest.main()
