"""
Root Cause Hypothesis Generator

Responsibilities
----------------
• Generate competing hypotheses
• Score confidence
• Link evidence
• Identify assumptions
• Recommend validation experiments

This module DOES NOT choose the correct hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .prompts import PROMPTS
from .schemas import Evidence, ProblemStatement


# ============================================================
# Models
# ============================================================


@dataclass(slots=True)
class ValidationExperiment:

    title: str

    description: str

    expected_signal: str

    success_metric: str

    effort: str


@dataclass(slots=True)
class RootCauseHypothesis:

    id: str

    title: str

    description: str

    confidence: float

    supporting_evidence: List[str]

    contradicting_evidence: List[str]

    assumptions: List[str]

    experiments: List[ValidationExperiment] = field(
        default_factory=list
    )


@dataclass(slots=True)
class HypothesisResult:

    hypotheses: List[RootCauseHypothesis]

    recommended_primary: str

    overall_confidence: float


# ============================================================
# LLM Generator
# ============================================================


class LLMHypothesisGenerator:

    async def generate(
        self,
        problem: ProblemStatement,
        evidence: List[Evidence],
    ) -> HypothesisResult:

        evidence_text = "\n".join(
            doc.content
            for doc in evidence
        )

        prompt = PROMPTS["hypothesis"].render(
            problem=problem.statement,
            evidence=evidence_text,
        )

        #
        # TODO
        #
        # response = await llm.generate(prompt)
        # parse structured JSON
        #

        evidence_ids = [
            doc.id
            for doc in evidence[:3]
        ]

        h1 = RootCauseHypothesis(

            id="hyp_001",

            title="Onboarding Complexity",

            description=(
                "Users abandon onboarding because "
                "they do not understand the required steps."
            ),

            confidence=0.88,

            supporting_evidence=evidence_ids,

            contradicting_evidence=[],

            assumptions=[
                "Users are motivated to finish onboarding."
            ],

            experiments=[
                ValidationExperiment(
                    title="Simplify onboarding",
                    description=(
                        "Reduce the number of required setup steps."
                    ),
                    expected_signal=(
                        "Higher onboarding completion."
                    ),
                    success_metric="Activation Rate",
                    effort="Medium",
                )
            ],
        )

        h2 = RootCauseHypothesis(

            id="hyp_002",

            title="Poor Value Communication",

            description=(
                "Users do not immediately understand the value."
            ),

            confidence=0.76,

            supporting_evidence=evidence_ids,

            contradicting_evidence=[],

            assumptions=[
                "Users leave before reaching first value."
            ],

            experiments=[
                ValidationExperiment(
                    title="Improve first value messaging",
                    description=(
                        "Expose value proposition earlier."
                    ),
                    expected_signal=(
                        "Lower abandonment."
                    ),
                    success_metric="Activation Rate",
                    effort="Low",
                )
            ],
        )

        h3 = RootCauseHypothesis(

            id="hyp_003",

            title="Technical Friction",

            description=(
                "Performance or reliability issues "
                "cause users to abandon onboarding."
            ),

            confidence=0.61,

            supporting_evidence=evidence_ids,

            contradicting_evidence=[],

            assumptions=[
                "Performance affects completion."
            ],

            experiments=[
                ValidationExperiment(
                    title="Measure page latency",
                    description=(
                        "Track load time during onboarding."
                    ),
                    expected_signal=(
                        "Latency correlates with drop-off."
                    ),
                    success_metric="Page Load Time",
                    effort="Low",
                )
            ],
        )

        hypotheses = [h1, h2, h3]

        hypotheses.sort(
            key=lambda h: h.confidence,
            reverse=True,
        )

        return HypothesisResult(

            hypotheses=hypotheses,

            recommended_primary=hypotheses[0].id,

            overall_confidence=(
                sum(
                    h.confidence
                    for h in hypotheses
                )
                / len(hypotheses)
            ),
        )


# ============================================================
# Validator
# ============================================================


class HypothesisValidator:

    def validate(
        self,
        result: HypothesisResult,
    ) -> list[str]:

        issues = []

        if len(result.hypotheses) < 3:

            issues.append(
                "Generate at least three competing hypotheses."
            )

        for hypothesis in result.hypotheses:

            if hypothesis.confidence < 0.50:

                issues.append(
                    f"{hypothesis.id} confidence is very low."
                )

            if not hypothesis.supporting_evidence:

                issues.append(
                    f"{hypothesis.id} has no supporting evidence."
                )

            if not hypothesis.experiments:

                issues.append(
                    f"{hypothesis.id} has no validation experiment."
                )

        return issues


# ============================================================
# Public Service
# ============================================================


class HypothesisService:

    def __init__(self):

        self.generator = LLMHypothesisGenerator()

        self.validator = HypothesisValidator()

    async def run(
        self,
        problem: ProblemStatement,
        evidence: List[Evidence],
    ) -> HypothesisResult:

        result = await self.generator.generate(
            problem,
            evidence,
        )

        issues = self.validator.validate(
            result
        )

        #
        # In production:
        # - attach issues to AI evals
        # - log metrics
        # - retry if severe
        #

        if issues:
            print(
                "Hypothesis Validation Issues:",
                issues,
            )

        return result