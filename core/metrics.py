"""
Metrics collection for the ProductPilot Discovery Agent.

Responsibilities
----------------
• Runtime metrics
• Cost metrics
• Retrieval metrics
• Quality metrics
• Product metrics
• Export structured metrics

No business logic belongs here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any

from .evaluator import EvaluationResult
from .hypothesis_generator import HypothesisResult
from .opportunity_scorer import OpportunityResult
from .problem_extractor import ProblemExtraction
from .schemas import Evidence
from .utils import estimate_tokens, utc_timestamp


# ============================================================
# Runtime
# ============================================================


@dataclass(slots=True)
class RuntimeMetrics:

    latency_ms: float = 0

    token_input: int = 0

    token_output: int = 0

    estimated_cost_usd: float = 0

    retries: int = 0

    timestamp: str = ""


# ============================================================
# Retrieval
# ============================================================


@dataclass(slots=True)
class RetrievalMetrics:

    retrieved_documents: int = 0

    unique_documents: int = 0

    average_relevance: float = 0

    average_confidence: float = 0

    average_trust: float = 0

    evidence_coverage: float = 0


# ============================================================
# Quality
# ============================================================


@dataclass(slots=True)
class QualityMetrics:

    evaluation_score: float = 0

    hallucination_risk: float = 0

    hypothesis_confidence: float = 0

    discovery_confidence: float = 0

    opportunity_score: float = 0

    priority_score: float = 0


# ============================================================
# Discovery
# ============================================================


@dataclass(slots=True)
class DiscoveryMetrics:

    problem_statement_length: int = 0

    evidence_count: int = 0

    assumptions_count: int = 0

    hypotheses_count: int = 0

    jtbd_count: int = 3

    recommendations_count: int = 0


# ============================================================
# Final Metrics
# ============================================================


@dataclass(slots=True)
class DiscoveryRunMetrics:

    runtime: RuntimeMetrics

    retrieval: RetrievalMetrics

    quality: QualityMetrics

    discovery: DiscoveryMetrics


# ============================================================
# Collector
# ============================================================


class MetricsCollector:

    def __init__(self):

        self._start = perf_counter()

    # --------------------------------------------------------

    def collect(

        self,

        prompt: str,

        response: str,

        evidence: list[Evidence],

        problem: ProblemExtraction,

        hypotheses: HypothesisResult,

        opportunity: OpportunityResult,

        evaluation: EvaluationResult,

    ) -> DiscoveryRunMetrics:

        runtime = RuntimeMetrics(

            latency_ms=self._latency(),

            token_input=estimate_tokens(prompt),

            token_output=estimate_tokens(response),

            estimated_cost_usd=self._estimate_cost(
                prompt,
                response,
            ),

            timestamp=utc_timestamp(),

        )

        retrieval = RetrievalMetrics(

            retrieved_documents=len(evidence),

            unique_documents=len(
                {
                    e.id
                    for e in evidence
                }
            ),

            average_relevance=self._average(
                [
                    e.relevance
                    for e in evidence
                ]
            ),

            average_confidence=self._average(
                [
                    e.confidence
                    for e in evidence
                ]
            ),

            average_trust=self._average(
                [
                    e.trust
                    for e in evidence
                ]
            ),

            evidence_coverage=min(
                len(evidence) / 5,
                1.0,
            ),

        )

        quality = QualityMetrics(

            evaluation_score=evaluation.overall_score,

            hallucination_risk=(
                1
                - evaluation.overall_score
            ),

            hypothesis_confidence=(
                hypotheses.overall_confidence
            ),

            discovery_confidence=(
                opportunity.confidence
            ),

            opportunity_score=(
                opportunity.opportunity_score
            ),

            priority_score=(
                opportunity.priority_score
            ),

        )

        discovery = DiscoveryMetrics(

            problem_statement_length=len(
                problem.problem.statement
            ),

            evidence_count=len(evidence),

            assumptions_count=len(
                problem.assumptions
            ),

            hypotheses_count=len(
                hypotheses.hypotheses
            ),

            recommendations_count=len(
                opportunity.reasoning
            ),

        )

        return DiscoveryRunMetrics(

            runtime=runtime,

            retrieval=retrieval,

            quality=quality,

            discovery=discovery,

        )

    # --------------------------------------------------------

    def export(

        self,

        metrics: DiscoveryRunMetrics,

    ) -> dict[str, Any]:

        return asdict(metrics)

    # --------------------------------------------------------

    def _latency(self) -> float:

        return round(
            (
                perf_counter()
                - self._start
            )
            * 1000,
            2,
        )

    # --------------------------------------------------------

    def _estimate_cost(

        self,

        prompt: str,

        response: str,

    ) -> float:

        #
        # Placeholder.
        #
        # Replace with provider-specific pricing.
        #

        tokens = (
            estimate_tokens(prompt)
            + estimate_tokens(response)
        )

        return round(
            tokens * 0.000002,
            6,
        )

    # --------------------------------------------------------

    @staticmethod
    def _average(

        values: list[float],

    ) -> float:

        if not values:

            return 0

        return round(

            sum(values)

            / len(values),

            3,

        )