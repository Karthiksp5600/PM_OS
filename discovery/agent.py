"""
Discovery Agent.

Public API for Product Discovery.
"""

from __future__ import annotations

from core.agent import BaseAgent
from core.metrics import MetricsCollector

from .evaluator import DiscoveryEvaluator
from .orchestrator import DiscoveryPipeline
from .schemas import (
    DiscoveryRequest,
    DiscoveryResponse,
)


class DiscoveryAgent(
    BaseAgent[
        DiscoveryRequest,
        DiscoveryResponse,
    ]
):

    def __init__(self):

        super().__init__(

            name="Discovery",

            workflow=DiscoveryPipeline(),

            evaluator=DiscoveryEvaluator(),

            metrics=MetricsCollector(),

        )

    async def execute(

        self,

        request: DiscoveryRequest,

    ) -> DiscoveryResponse:

        context = await self.workflow.run(
            request
        )

        return DiscoveryResponse(

            workflow_id=request.workflow_id,

            project_id=request.project_id,

            stage="discovery",

            intent=context.intent.intent,

            artifact=context.artifact,

            evaluations=context.evaluation.evaluations,

            metrics=context.metrics.runtime,

            completed_at=context.completed_at,

        )


async def run_discovery(
    request: DiscoveryRequest,
):

    return await DiscoveryAgent().run(
        request
    )