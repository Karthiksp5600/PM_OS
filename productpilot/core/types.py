"""Shared type definitions for the ProductPilot agent framework.

Contains enums, protocols, and type aliases reusable across all agents.
"""

from __future__ import annotations

from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
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
# Interfaces (Protocols)
# ---------------------------------------------------------------------


class Retriever(Protocol):
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
    ) -> Sequence[Any]:  # Returns Sequence of Evidence
        ...


class LLM(Protocol):
    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        ...


class Ranker(Protocol):
    async def rank(
        self,
        evidence: Sequence[Any],
    ) -> Sequence[Any]:
        ...


class Evaluator(Protocol):
    async def evaluate(
        self,
        artifact: Any,
    ) -> Sequence[Any]:  # Returns Sequence of EvaluationResult
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
