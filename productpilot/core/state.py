"""State management class for ProductPilot agent workflows.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowState(BaseModel):
    """The canonical runtime state passed along the execution pipeline."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    request: Any = None
    intent: Any = None
    evidence: list[Any] = Field(default_factory=list)
    problem: Any = None
    jtbd: Any = None
    hypotheses: Any = None
    opportunity: Any = None
    evaluation: Any = None
    metrics: Any = None

    # Extensibility bags for unstructured or agent-specific info
    artifacts: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)

    # Lifecycle completion tracking
    completed_at: Any = None
