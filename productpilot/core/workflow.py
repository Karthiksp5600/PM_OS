"""Generic Workflow Engine for executing agent pipelines.
"""

from __future__ import annotations

from typing import Any

from .pipeline import Pipeline
from .state import WorkflowState


class WorkflowEngine:
    """A generic reusable workflow runner for all AI agents."""

    def __init__(self, pipeline: Pipeline) -> None:
        self.pipeline = pipeline

    async def run(self, request: Any) -> WorkflowState:
        """Initialize the workflow state with a request and execute the pipeline."""
        state = WorkflowState(request=request)
        await self.pipeline.execute(state)
        return state
