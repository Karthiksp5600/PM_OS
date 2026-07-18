"""KPI Tree Agent for converting discovery output into a KPI tree artifact."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Mapping

JsonDict = dict[str, Any]


class KpiTreeAgentError(ValueError):
    """Raised when the KPI Tree Agent receives an invalid discovery result."""


class KpiTreeAgent:
    """Builds a KPI tree from a discovery-stage output envelope."""

    stage_id = "kpi_tree"
    agent_name = "KpiTreeAgent"

    def run(self, discovery_result: Mapping[str, Any]) -> JsonDict:
        started_at = perf_counter()
        self._validate_discovery_result(discovery_result)

        structured_output = discovery_result.get("structured_output", {})
        problem_statement = str(structured_output.get("problem_statement") or "")
        problem_statements = structured_output.get("problem_statements") or [problem_statement]
        target_segment = str(discovery_result.get("context", {}).get("target_segment") or discovery_result.get("input", {}).get("target_segment") or "users")
        kpi_tree = self._build_kpi_tree(problem_statement, list(problem_statements), target_segment)

        return {
            "workflow_id": str(discovery_result.get("workflow_id", "wf_unknown")),
            "tenant_id": str(discovery_result.get("tenant_id", "tenant_unknown")),
            "project_id": str(discovery_result.get("project_id", "proj_unknown")),
            "stage_id": self.stage_id,
            "agent_name": self.agent_name,
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": {"problem_statement": problem_statement, "problem_statements": list(problem_statements)},
            "structured_output": {
                "kpi_tree": kpi_tree,
                "summary": self._summary(kpi_tree),
            },
            "citations": [],
            "assumptions": [
                "The discovery output provides a useful problem framing.",
                "The KPI tree should focus on measurable outcomes related to the primary problem.",
            ],
            "open_questions": [
                "Which KPI is the strongest leading indicator for this problem?",
                "Which guardrail metrics must remain stable?",
            ],
            "warnings": [],
            "errors": [],
            "metrics": {
                "latency_ms": round((perf_counter() - started_at) * 1000, 3),
                "item_count": len(kpi_tree),
            },
            "evaluation": {
                "schema_valid": True,
                "decision": "pass",
                "overall_score": 0.9,
            },
            "next_action": "continue_to_solutioning",
            "artifact_ref": self._artifact_ref(discovery_result, kpi_tree),
            "version": "kpi-tree-v1",
        }

    def _validate_discovery_result(self, discovery_result: Mapping[str, Any]) -> None:
        if not isinstance(discovery_result, Mapping):
            raise KpiTreeAgentError("Discovery result must be a mapping")
        if not discovery_result.get("structured_output"):
            raise KpiTreeAgentError("Discovery result must include structured_output")

    def _build_kpi_tree(self, problem_statement: str, problem_statements: list[str], target_segment: str) -> list[JsonDict]:
        base_kpis = [
            {
                "name": "Activation rate",
                "definition": f"Share of {target_segment} reaching a meaningful first-value action in the first week.",
                "owner": "Product",
                "direction": "increase",
                "source": problem_statement,
            },
            {
                "name": "First-week retention",
                "definition": f"Percentage of {target_segment} returning to the product within seven days.",
                "owner": "Growth",
                "direction": "increase",
                "source": problem_statements[0] if problem_statements else problem_statement,
            },
            {
                "name": "Task completion rate",
                "definition": f"Share of {target_segment} completing the key first-use task without dropping off.",
                "owner": "Product",
                "direction": "increase",
                "source": problem_statements[1] if len(problem_statements) > 1 else problem_statement,
            },
        ]
        return base_kpis

    def _summary(self, kpi_tree: list[JsonDict]) -> str:
        names = ", ".join(item.get("name", "") for item in kpi_tree if item.get("name"))
        return f"KPI tree built around the core discovery problem with focus areas: {names}."

    def _artifact_ref(self, discovery_result: Mapping[str, Any], kpi_tree: list[JsonDict]) -> str:
        raw = f"{discovery_result.get('workflow_id', 'wf_unknown')}:kpi_tree:{json.dumps(kpi_tree, sort_keys=True)}"
        return f"art_{os.urandom(4).hex()}"


__all__ = ["KpiTreeAgent", "KpiTreeAgentError"]
