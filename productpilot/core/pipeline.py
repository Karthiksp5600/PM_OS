"""Pipeline execution manager for ProductPilot agent workflows.
"""

from __future__ import annotations

from .exceptions import StageExecutionError
from .stage import PipelineStage
from .state import WorkflowState


class Pipeline:
    """Orchestrates sequential execution of pipeline stages."""

    def __init__(self, stages: list[PipelineStage]) -> None:
        self.stages = stages

    async def execute(self, state: WorkflowState) -> None:
        """Run all registered pipeline stages sequentially on the shared state."""
        for stage in self.stages:
            try:
                # In a later step, we can wrap this in logging/metrics/event hooks
                await stage.execute(state)
            except Exception as exc:
                raise StageExecutionError(
                    message=f"Stage '{stage.name}' failed to execute: {exc}",
                    details={"stage": stage.name},
                ) from exc
