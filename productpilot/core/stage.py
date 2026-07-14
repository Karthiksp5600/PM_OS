"""Base class for all pipeline stages in ProductPilot.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .state import WorkflowState


class PipelineStage(ABC):
    """Abstract base class representing a single step/stage in an agent's execution pipeline."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The identifier name of the stage (e.g. 'intent', 'retrieval')."""
        pass

    @abstractmethod
    async def execute(self, state: WorkflowState) -> None:
        """Run the business or LLM logic of this stage, reading from and writing to the state."""
        pass
