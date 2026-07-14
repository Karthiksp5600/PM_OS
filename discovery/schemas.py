"""
Pydantic schemas for the ProductPilot Discovery Agent.

This module defines the canonical request and response models shared
across the Discovery pipeline.

Python 3.12+
Pydantic v2
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .types import (
    ConfidenceLevel,
    DiscoveryIntent,
    EvaluationStatus,
    JourneyStage,
    OpportunityLevel,
    PersonaType,
    SourceType,
    WorkflowMode,
)


# =====================================================================
# Base Model
# =====================================================================


class PPBaseModel(BaseModel):
    """Base model used throughout ProductPilot."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
    )


# =====================================================================
# User Intent
# =====================================================================


class UserIntent(PPBaseModel):

    goal: str | None = None

    feedback_summary: str | None = None

    analytics_problem: str | None = None

    desired_outcome: str | None = None

    business_goal: str | None = None


# =====================================================================
# Company Context
# =====================================================================


class CompanyContext(PPBaseModel):

    company_name: str | None = None

    product_name: str | None = None

    north_star_metric: str | None = None

    strategy_summary: str | None = None

    roadmap_summary: str | None = None

    existing_constraints: list[str] = Field(default_factory=list)


# =====================================================================
# Retrieval Context
# =====================================================================


class RetrievalContext(PPBaseModel):

    retrieval_refs: list[str] = Field(default_factory=list)

    company_context_refs: list[str] = Field(default_factory=list)

    previous_prd_refs: list[str] = Field(default_factory=list)

    interview_refs: list[str] = Field(default_factory=list)

    analytics_refs: list[str] = Field(default_factory=list)

    source_notes: str | None = None


# =====================================================================
# Instructions
# =====================================================================


class DiscoveryInstructions(PPBaseModel):

    task: str

    constraints: list[str] = Field(default_factory=list)

    success_criteria: list[str] = Field(default_factory=list)

    output_style: str = "structured"


# =====================================================================
# Budgets
# =====================================================================


class BudgetConfig(PPBaseModel):

    token_budget: int

    latency_budget_ms: int

    retry_limit: int = 0

    cost_budget_usd: float | None = None


# =====================================================================
# Policy
# =====================================================================


class PolicyConfig(PPBaseModel):

    approval_required: bool = True

    can_publish: bool = False

    can_write_memory: bool = False

    sensitivity: str = "internal"


# =====================================================================
# Discovery Request
# =====================================================================


class DiscoveryRequest(PPBaseModel):

    workflow_id: str

    tenant_id: str

    project_id: str

    workflow_mode: WorkflowMode

    user_intent: UserIntent

    company_context: CompanyContext

    retrieval_context: RetrievalContext

    instructions: DiscoveryInstructions

    budgets: BudgetConfig

    policy: PolicyConfig


# =====================================================================
# Evidence
# =====================================================================


class Evidence(PPBaseModel):

    id: str

    title: str

    content: str

    source_type: SourceType

    confidence: float = Field(ge=0, le=1)

    relevance: float = Field(ge=0, le=1)

    freshness: float = Field(ge=0, le=1)

    trust: float = Field(ge=0, le=1)

    metadata: dict[str, Any] = Field(default_factory=dict)


# =====================================================================
# JTBD
# =====================================================================


class JTBD(PPBaseModel):

    actor: str

    situation: str

    motivation: str

    expected_outcome: str


# =====================================================================
# Problem Statement
# =====================================================================


class ProblemStatement(PPBaseModel):

    title: str

    statement: str

    why_now: str

    affected_personas: list[PersonaType] = Field(default_factory=list)

    journey_stage: JourneyStage = JourneyStage.UNKNOWN


# =====================================================================
# Assumption
# =====================================================================


class Assumption(PPBaseModel):

    statement: str

    confidence: ConfidenceLevel

    evidence_ids: list[str] = Field(default_factory=list)


# =====================================================================
# Hypothesis
# =====================================================================


class RootCauseHypothesis(PPBaseModel):

    hypothesis: str

    confidence: float = Field(ge=0, le=1)

    evidence_ids: list[str] = Field(default_factory=list)

    assumptions: list[str] = Field(default_factory=list)


# =====================================================================
# Opportunity Score
# =====================================================================


class OpportunityScore(PPBaseModel):

    reach: float = Field(ge=0, le=10)

    severity: float = Field(ge=0, le=10)

    frequency: float = Field(ge=0, le=10)

    strategic_alignment: float = Field(ge=0, le=10)

    revenue_impact: float = Field(ge=0, le=10)

    retention_impact: float = Field(ge=0, le=10)

    confidence: float = Field(ge=0, le=1)

    risk: float = Field(ge=0, le=10)

    weighted_score: float

    level: OpportunityLevel


# =====================================================================
# Open Question
# =====================================================================


class OpenQuestion(PPBaseModel):

    question: str

    priority: int = Field(ge=1, le=5)


# =====================================================================
# AI Evaluation
# =====================================================================


class EvaluationItem(PPBaseModel):

    name: str

    status: EvaluationStatus

    score: float = Field(ge=0, le=1)

    reason: str


# =====================================================================
# Runtime Metrics
# =====================================================================


class RuntimeMetrics(PPBaseModel):

    latency_ms: float

    token_input: int

    token_output: int

    cost_usd: float

    retrieval_count: int

    citation_count: int

    retry_count: int


# =====================================================================
# Discovery Artifact
# =====================================================================


class DiscoveryArtifact(PPBaseModel):

    problem: ProblemStatement

    jtbd: JTBD | None = None

    evidence: list[Evidence] = Field(default_factory=list)

    assumptions: list[Assumption] = Field(default_factory=list)

    hypotheses: list[RootCauseHypothesis] = Field(default_factory=list)

    opportunity: OpportunityScore

    recommended_kpis: list[str] = Field(default_factory=list)

    open_questions: list[OpenQuestion] = Field(default_factory=list)

    discovery_confidence: float = Field(ge=0, le=1)


# =====================================================================
# Final Response
# =====================================================================


class DiscoveryResponse(PPBaseModel):

    workflow_id: str

    project_id: str

    stage: str = "discovery"

    intent: DiscoveryIntent

    artifact: DiscoveryArtifact

    evaluations: list[EvaluationItem]

    metrics: RuntimeMetrics

    completed_at: datetime

    version: str = "0.1.0"