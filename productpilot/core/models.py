"""Canonical data models for the ProductPilot agent framework.

Consolidates all shared schemas into single, unified Pydantic models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .types import (
    EvaluationStatus,
    OpportunityLevel,
    SourceType,
)


class PPBaseModel(BaseModel):
    """Base model used throughout ProductPilot for Pydantic v2."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


# ---------------------------------------------------------------------
# Evidence Model
# ---------------------------------------------------------------------


class Evidence(PPBaseModel):
    """Canonical model representing retrieved user/market feedback or facts."""

    id: str
    title: str
    content: str
    source_type: SourceType
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness: float = Field(default=0.0, ge=0.0, le=1.0)
    trust: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------
# Metrics Model
# ---------------------------------------------------------------------


class RuntimeMetrics(PPBaseModel):
    """Canonical model for tracking agent execution performance."""

    latency_ms: float = 0.0
    token_input: int = 0
    token_output: int = 0
    cost_usd: float = 0.0
    estimated_cost_usd: float = 0.0
    retries: int = 0
    retry_count: int = 0
    retrieval_count: int = 0
    citation_count: int = 0
    timestamp: str | datetime = ""


# ---------------------------------------------------------------------
# Evaluation Model
# ---------------------------------------------------------------------


class EvaluationResult(PPBaseModel):
    """Canonical model for a single evaluation check result."""

    name: str
    status: EvaluationStatus
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str


# ---------------------------------------------------------------------
# Opportunity Score Model
# ---------------------------------------------------------------------


class OpportunityScore(PPBaseModel):
    """Canonical model for prioritising product opportunities."""

    reach: float = Field(default=0.0, ge=0.0, le=10.0)
    severity: float = Field(default=0.0, ge=0.0, le=10.0)
    frequency: float = Field(default=0.0, ge=0.0, le=10.0)
    strategic_alignment: float = Field(default=0.0, ge=0.0, le=10.0)
    revenue_impact: float = Field(default=0.0, ge=0.0, le=10.0)
    retention_impact: float = Field(default=0.0, ge=0.0, le=10.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    risk: float = Field(default=0.0, ge=0.0, le=10.0)
    weighted_score: float = 0.0
    level: OpportunityLevel | None = None


# ---------------------------------------------------------------------
# Generic Agent Response
# ---------------------------------------------------------------------

ArtifactT = TypeVar("ArtifactT")


class AgentResponse(PPBaseModel, Generic[ArtifactT]):
    """Generic envelope returned by every ProductPilot agent execution."""

    workflow_id: str
    project_id: str
    stage: str
    artifact: ArtifactT
    evaluations: list[EvaluationResult] = Field(default_factory=list)
    metrics: RuntimeMetrics = Field(default_factory=RuntimeMetrics)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "0.1.0"
