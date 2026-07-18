"""Concrete orchestrator for running ProductPilot workflows."""

from __future__ import annotations

from typing import Any, Mapping

from productpilot.agents.discovery_agent import DiscoveryAgent
from productpilot.agents.kpi_tree_agent import KpiTreeAgent

from .logger import TraceContext, create_logger, stage_completed, stage_started
from .state import WorkflowState

logger = create_logger("productpilot.orchestrator")


class ProductPilotOrchestrator:
    """Runs a discovery-first workflow and stores stage outputs in shared state."""

    def __init__(self, discovery_agent: DiscoveryAgent | None = None, kpi_tree_agent: KpiTreeAgent | None = None) -> None:
        self.discovery_agent = discovery_agent or DiscoveryAgent()
        self.kpi_tree_agent = kpi_tree_agent or KpiTreeAgent()

    def run(self, request: Mapping[str, Any]) -> WorkflowState:
        trace = TraceContext(
            workflow_id=str(request.get("workflow_id", "wf_unknown")),
            project_id=str(request.get("project_id", "proj_unknown")),
        )
        state = WorkflowState(request=dict(request))
        state.context["trace"] = trace

        stage_started("discovery", trace)
        discovery_result = self.discovery_agent.run(request)
        state.artifacts["discovery"] = discovery_result
        state.context["discovery"] = discovery_result
        stage_completed("discovery", trace, metadata={"artifact_ref": discovery_result.get("artifact_ref")})

        stage_started("kpi_tree", trace)
        kpi_tree_result = self.kpi_tree_agent.run(discovery_result)
        state.artifacts["kpi_tree"] = kpi_tree_result
        state.context["kpi_tree"] = kpi_tree_result
        state.problem = discovery_result.get("structured_output", {}).get("problem_statement")
        state.evaluation = kpi_tree_result.get("evaluation")
        state.metrics = {
            "discovery": discovery_result.get("metrics"),
            "kpi_tree": kpi_tree_result.get("metrics"),
        }
        stage_completed("kpi_tree", trace, metadata={"artifact_ref": kpi_tree_result.get("artifact_ref")})

        logger.info("workflow completed", extra={"workflow_id": trace.workflow_id, "project_id": trace.project_id, "stage": "workflow"})
        return state
