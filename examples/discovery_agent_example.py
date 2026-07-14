"""Run the ProductPilot Discovery Agent with a sample goal-driven request."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from productpilot.agents import DiscoveryAgent


def main() -> None:
    request = {
        "workflow_id": "wf_activation_001",
        "tenant_id": "tenant_acme",
        "project_id": "proj_growth",
        "entry_mode": "goal_driven",
        "target_segment": "new workspace admins",
        "time_horizon": "the next quarter",
        "user_intent": {
            "goal": "Increase activation in the first 7 days for new B2B workspaces.",
            "feedback_summary": None,
        },
        "context": {
            "company_context_refs": ["doc_activation_strategy"],
            "prior_stage_refs": [],
            "retrieval_refs": ["rag_onboarding_dropoff", "rag_admin_feedback"],
            "memory_refs": ["mem_prd_style"],
            "source_notes": (
                "Analytics show a steep drop-off before invite completion. "
                "Support notes mention that workspace admins are unsure what setup step creates first value."
            ),
        },
        "instructions": {
            "task": "Frame the discovery problem for activation improvement.",
            "constraints": [
                "Do not propose final solutions yet.",
                "Ground every major claim in available context.",
            ],
            "success_criteria": [
                "Clear problem statement",
                "Explicit assumptions",
                "Reviewable open questions",
            ],
            "output_style": "concise_product_discovery",
        },
        "budgets": {
            "token_budget": 4000,
            "latency_budget_ms": 120000,
            "retry_count": 0,
            "cost_budget_usd": 0.25,
        },
        "policy": {
            "approval_required": True,
            "can_write_memory": False,
            "can_publish": False,
            "sensitivity": "internal",
        },
    }

    result = DiscoveryAgent().run(request)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
