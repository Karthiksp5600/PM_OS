"""State management class for ProductPilot agent workflows.
"""

from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:  # pragma: no cover - exercised in minimal environments
    class BaseModel:  # type: ignore[override]
        """Minimal BaseModel fallback for environments without pydantic."""

        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> dict[str, Any]:
            return dict(self.__dict__)

        def dict(self) -> dict[str, Any]:
            return self.model_dump()

    def ConfigDict(**_: Any) -> dict[str, Any]:
        return {}

    def Field(*args: Any, **kwargs: Any) -> Any:
        default = kwargs.get("default")
        default_factory = kwargs.get("default_factory")
        if default_factory is not None:
            return default_factory()
        return default


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

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
