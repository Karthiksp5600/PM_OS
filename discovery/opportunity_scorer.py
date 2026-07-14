"""
Opportunity Scoring Engine.

Responsibilities
----------------
• Estimate business opportunity
• Estimate customer value
• Estimate confidence
• Estimate implementation risk
• Generate Opportunity and Priority scores

This module does NOT prioritize the roadmap.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .config import settings
from .schemas import Evidence
from .problem_extractor import ProblemExtraction
from .hypothesis_generator import HypothesisResult


# ============================================================
# Models
# ============================================================


@dataclass(slots=True)
class OpportunityBreakdown:

    reach: float

    severity: float

    frequency: float

    strategic_alignment: float

    revenue_impact: float

    retention_impact: float

    evidence_quality: float

    confidence: float

    implementation_risk: float

    implementation_cost: float

    time_to_value: float


@dataclass(slots=True)
class OpportunityResult:

    breakdown: OpportunityBreakdown

    opportunity_score: float

    priority_score: float

    confidence: float

    reasoning: list[str]


# ============================================================
# Scorer
# ============================================================


class OpportunityScorer:

    def score(

        self,

        problem: ProblemExtraction,

        evidence: list[Evidence],

        hypotheses: HypothesisResult,

    ) -> OpportunityResult:

        breakdown = OpportunityBreakdown(

            reach=self._reach(problem),

            severity=self._severity(problem),

            frequency=self._frequency(evidence),

            strategic_alignment=self._strategy(problem),

            revenue_impact=self._revenue(problem),

            retention_impact=self._retention(problem),

            evidence_quality=self._evidence_quality(evidence),

            confidence=hypotheses.overall_confidence,

            implementation_risk=self._risk(hypotheses),

            implementation_cost=self._cost(problem),

            time_to_value=self._time_to_value(problem),

        )

        opportunity = self._opportunity_score(
            breakdown
        )

        priority = self._priority_score(
            breakdown,
            opportunity,
        )

        return OpportunityResult(

            breakdown=breakdown,

            opportunity_score=round(
                opportunity,
                2,
            ),

            priority_score=round(
                priority,
                2,
            ),

            confidence=round(
                hypotheses.overall_confidence,
                2,
            ),

            reasoning=self._reasoning(
                breakdown
            ),
        )

    # -------------------------------------------------------

    def _reach(
        self,
        problem,
    ) -> float:

        return 8.0

    # -------------------------------------------------------

    def _severity(
        self,
        problem,
    ) -> float:

        return 8.5

    # -------------------------------------------------------

    def _frequency(
        self,
        evidence,
    ) -> float:

        if not evidence:
            return 3.0

        return min(
            10,
            6 + len(evidence) * 0.3,
        )

    # -------------------------------------------------------

    def _strategy(
        self,
        problem,
    ) -> float:

        return 8.0

    # -------------------------------------------------------

    def _revenue(
        self,
        problem,
    ) -> float:

        return 6.5

    # -------------------------------------------------------

    def _retention(
        self,
        problem,
    ) -> float:

        return 7.5

    # -------------------------------------------------------

    def _evidence_quality(
        self,
        evidence,
    ) -> float:

        if not evidence:
            return 0

        return mean(
            [
                (
                    e.confidence
                    + e.relevance
                    + e.trust
                )
                / 3
                for e in evidence
            ]
        ) * 10

    # -------------------------------------------------------

    def _risk(
        self,
        hypotheses,
    ) -> float:

        confidence = hypotheses.overall_confidence

        return (1 - confidence) * 10

    # -------------------------------------------------------

    def _cost(
        self,
        problem,
    ) -> float:

        return 5.0

    # -------------------------------------------------------

    def _time_to_value(
        self,
        problem,
    ) -> float:

        return 7.0

    # -------------------------------------------------------

    def _opportunity_score(
        self,
        b: OpportunityBreakdown,
    ) -> float:

        weights = settings.opportunity

        weighted_sum = (

            b.reach * weights.reach +

            b.severity * weights.severity +

            b.frequency * weights.frequency +

            b.strategic_alignment
            * weights.strategic_alignment +

            b.revenue_impact
            * weights.revenue +

            b.retention_impact
            * weights.retention +

            (b.confidence * 10)
            * weights.confidence +

            (10 - b.implementation_risk)
            * weights.risk

        )

        return weighted_sum

    # -------------------------------------------------------

    def _priority_score(

        self,

        breakdown,

        opportunity,

    ) -> float:

        return (

            opportunity

            * (10 - breakdown.implementation_cost)

            * breakdown.time_to_value

        ) / 100

    # -------------------------------------------------------

    def _reasoning(

        self,

        b,

    ) -> list[str]:

        reasons = []

        if b.reach >= 8:

            reasons.append(
                "Large customer reach."
            )

        if b.severity >= 8:

            reasons.append(
                "High customer pain."
            )

        if b.strategic_alignment >= 8:

            reasons.append(
                "Strong strategic alignment."
            )

        if b.implementation_risk <= 3:

            reasons.append(
                "Low implementation risk."
            )

        if b.evidence_quality >= 8:

            reasons.append(
                "High quality supporting evidence."
            )

        return reasons