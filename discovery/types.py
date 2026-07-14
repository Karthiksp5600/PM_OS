"""
Shared type definitions for the ProductPilot Discovery Agent.

This module intentionally contains NO business logic.

Everything here should be reusable across the Discovery package and
eventually the rest of ProductPilot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    TypeAlias,
)

# ---------------------------------------------------------------------
# Generic JSON Types
# ---------------------------------------------------------------------

JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | Dict[str, "JSONValue"] | List["JSONValue"]

JSONObject: TypeAlias = Dict[str, JSONValue]

# ---------------------------------------------------------------------
# Workflow Modes
# ---------------------------------------------------------------------


class WorkflowMode(str, Enum):
    GOAL_DRIVEN = "goal_driven"
    FEEDBACK_DRIVEN = "feedback_driven"
    ANALYTICS_DRIVEN = "analytics_driven"


# ---------------------------------------------------------------------
# Discovery Intent
# ---------------------------------------------------------------------


class DiscoveryIntent(str, Enum):

    GROWTH = "growth"

    RETENTION = "retention"

    REVENUE = "revenue"

    ENGAGEMENT = "engagement"

    ACTIVATION = "activation"

    PLATFORM = "platform"

    UX = "ux"

    BUG = "bug"

    PERFORMANCE = "performance"

    RESEARCH = "research"

    COMPLIANCE = "compliance"

    INTERNAL_TOOL = "internal_tool"

    UNKNOWN = "unknown"


# ---------------------------------------------------------------------
# Source Types
# ---------------------------------------------------------------------


class SourceType(str, Enum):

    RAG = "rag"

    CUSTOMER_FEEDBACK = "customer_feedback"

    SUPPORT = "support"

    ROADMAP = "roadmap"

    PRD = "prd"

    ANALYTICS = "analytics"

    STRATEGY = "strategy"

    OKR = "okr"

    INTERVIEW = "interview"

    MEMORY = "memory"

    MANUAL = "manual"

    UNKNOWN = "unknown"


# ---------------------------------------------------------------------
# Evaluation Results
# ---------------------------------------------------------------------


class EvaluationStatus(str, Enum):

    PASS = "pass"

    WARN = "warn"

    FAIL = "fail"


# ---------------------------------------------------------------------
# Confidence Levels
# ---------------------------------------------------------------------


class ConfidenceLevel(str, Enum):

    VERY_LOW = "very_low"

    LOW = "low"

    MEDIUM = "medium"

    HIGH = "high"

    VERY_HIGH = "very_high"


# ---------------------------------------------------------------------
# Opportunity Levels
# ---------------------------------------------------------------------


class OpportunityLevel(str, Enum):

    LOW = "low"

    MEDIUM = "medium"

    HIGH = "high"

    VERY_HIGH = "very_high"


# ---------------------------------------------------------------------
# Persona Types
# ---------------------------------------------------------------------


class PersonaType(str, Enum):

    ADMIN = "admin"

    END_USER = "end_user"

    MANAGER = "manager"

    EXECUTIVE = "executive"

    DEVELOPER = "developer"

    OPERATOR = "operator"

    UNKNOWN = "unknown"


# ---------------------------------------------------------------------
# Journey Stages
# ---------------------------------------------------------------------


class JourneyStage(str, Enum):

    DISCOVERY = "discovery"

    SIGNUP = "signup"

    ONBOARDING = "onboarding"

    ACTIVATION = "activation"

    ENGAGEMENT = "engagement"

    RETENTION = "retention"

    EXPANSION = "expansion"

    CHURN = "churn"

    UNKNOWN = "unknown"


# ---------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------


@dataclass(slots=True)
class Evidence:

    id: str

    source_type: SourceType

    title: str

    content: str

    confidence: float

    relevance: float

    freshness: float

    trust: float

    metadata: Mapping[str, Any]


# ---------------------------------------------------------------------
# Hypothesis
# ---------------------------------------------------------------------


@dataclass(slots=True)
class Hypothesis:

    id: str

    statement: str

    confidence: float

    supporting_evidence: Sequence[str]

    assumptions: Sequence[str]


# ---------------------------------------------------------------------
# Opportunity Score
# ---------------------------------------------------------------------


@dataclass(slots=True)
class OpportunityScore:

    reach: float

    severity: float

    frequency: float

    strategic_alignment: float

    revenue_impact: float

    retention_impact: float

    confidence: float

    risk: float

    weighted_score: float


# ---------------------------------------------------------------------
# Evaluation Result
# ---------------------------------------------------------------------


@dataclass(slots=True)
class EvaluationResult:

    name: str

    status: EvaluationStatus

    score: float

    reason: str


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------


@dataclass(slots=True)
class RuntimeMetrics:

    latency_ms: float

    token_input: int

    token_output: int

    cost_usd: float

    retries: int

    timestamp: datetime


# ---------------------------------------------------------------------
# Retrieval Interface
# ---------------------------------------------------------------------


class Retriever(Protocol):

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
    ) -> Sequence[Evidence]:
        ...


# ---------------------------------------------------------------------
# LLM Interface
# ---------------------------------------------------------------------


class LLM(Protocol):

    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        ...


# ---------------------------------------------------------------------
# Ranker Interface
# ---------------------------------------------------------------------


class Ranker(Protocol):

    async def rank(
        self,
        evidence: Sequence[Evidence],
    ) -> Sequence[Evidence]:
        ...


# ---------------------------------------------------------------------
# Evaluator Interface
# ---------------------------------------------------------------------


class Evaluator(Protocol):

    async def evaluate(
        self,
        artifact: Any,
    ) -> Sequence[EvaluationResult]:
        ...


# ---------------------------------------------------------------------
# Shared Literals
# ---------------------------------------------------------------------

PipelineStage = Literal[
    "intent",
    "retrieval",
    "ranking",
    "problem",
    "jtbd",
    "hypothesis",
    "opportunity",
    "evaluation",
]

ArtifactType = Literal[
    "problem_statement",
    "discovery_report",
    "hypothesis",
    "opportunity_score",
]