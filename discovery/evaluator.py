"""
AI Evaluation framework for ProductPilot Discovery.

Responsibilities
----------------
• Validate discovery artifacts
• Run independent evaluation checks
• Produce quality scores
• Recommend retries
• Support future LLM-as-a-Judge evaluation

This module NEVER modifies artifacts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .hypothesis_generator import HypothesisResult
from .jtbd import JTBDResult
from .opportunity_scorer import OpportunityResult
from .problem_extractor import ProblemExtraction
from .schemas import Evidence


# ============================================================
# Models
# ============================================================


@dataclass(slots=True)
class Evaluation:

    name: str

    score: float

    passed: bool

    message: str


@dataclass(slots=True)
class EvaluationResult:

    evaluations: list[Evaluation]

    overall_score: float

    passed: bool

    retry_recommended: bool

    reasoning: list[str]


# ============================================================
# Base Evaluator
# ============================================================


class BaseEvaluator(ABC):

    @abstractmethod
    def evaluate(
        self,
        context,
    ) -> Evaluation:
        pass


# ============================================================
# Schema
# ============================================================


class SchemaEvaluator(BaseEvaluator):

    def evaluate(
        self,
        context,
    ) -> Evaluation:

        passed = (

            context.problem.problem.statement != ""

            and len(context.evidence) > 0

        )

        return Evaluation(

            name="Schema",

            score=1.0 if passed else 0.0,

            passed=passed,

            message="Required fields present."
            if passed
            else "Missing required fields.",
        )


# ============================================================
# Evidence
# ============================================================


class EvidenceEvaluator(BaseEvaluator):

    def evaluate(
        self,
        context,
    ) -> Evaluation:

        supported = len(context.evidence)

        score = min(
            supported / 5,
            1.0,
        )

        return Evaluation(

            name="Evidence Coverage",

            score=score,

            passed=score >= 0.70,

            message=f"{supported} evidence items.",
        )


# ============================================================
# Logic
# ============================================================


class LogicEvaluator(BaseEvaluator):

    def evaluate(
        self,
        context,
    ) -> Evaluation:

        score = context.opportunity.confidence

        return Evaluation(

            name="Business Logic",

            score=score,

            passed=score >= 0.70,

            message="Business reasoning evaluated.",
        )


# ============================================================
# JTBD
# ============================================================


class JTBDEvaluator(BaseEvaluator):

    def evaluate(
        self,
        context,
    ) -> Evaluation:

        score = min(

            context.jtbd.functional.confidence,

            context.jtbd.emotional.confidence,

            context.jtbd.social.confidence,

        )

        return Evaluation(

            name="JTBD",

            score=score,

            passed=score >= 0.70,

            message="JTBD quality evaluated.",
        )


# ============================================================
# Hypothesis
# ============================================================


class HypothesisEvaluator(BaseEvaluator):

    def evaluate(
        self,
        context,
    ) -> Evaluation:

        score = context.hypotheses.overall_confidence

        return Evaluation(

            name="Hypotheses",

            score=score,

            passed=score >= 0.70,

            message="Multiple hypotheses generated.",
        )


# ============================================================
# Opportunity
# ============================================================


class OpportunityEvaluator(BaseEvaluator):

    def evaluate(
        self,
        context,
    ) -> Evaluation:

        score = min(

            context.opportunity.opportunity_score / 10,

            1.0,

        )

        return Evaluation(

            name="Opportunity",

            score=score,

            passed=score >= 0.60,

            message="Opportunity score validated.",
        )


# ============================================================
# Hallucination
# ============================================================


class HallucinationEvaluator(BaseEvaluator):

    def evaluate(
        self,
        context,
    ) -> Evaluation:

        unsupported = 0

        for hypothesis in context.hypotheses.hypotheses:

            if not hypothesis.supporting_evidence:

                unsupported += 1

        if unsupported == 0:

            return Evaluation(

                name="Hallucination",

                score=1.0,

                passed=True,

                message="Every hypothesis references evidence.",
            )

        score = max(
            0,
            1 - unsupported / len(context.hypotheses.hypotheses),
        )

        return Evaluation(

            name="Hallucination",

            score=score,

            passed=score >= 0.80,

            message=f"{unsupported} unsupported hypotheses.",
        )


# ============================================================
# Discovery Context
# ============================================================


@dataclass(slots=True)
class EvaluationContext:

    problem: ProblemExtraction

    evidence: list[Evidence]

    jtbd: JTBDResult

    hypotheses: HypothesisResult

    opportunity: OpportunityResult


# ============================================================
# Main Evaluator
# ============================================================


class DiscoveryEvaluator:

    def __init__(self):

        self.evaluators = [

            SchemaEvaluator(),

            EvidenceEvaluator(),

            LogicEvaluator(),

            JTBDEvaluator(),

            HypothesisEvaluator(),

            OpportunityEvaluator(),

            HallucinationEvaluator(),

        ]

    def evaluate(

        self,

        context: EvaluationContext,

    ) -> EvaluationResult:

        results = [

            evaluator.evaluate(context)

            for evaluator in self.evaluators

        ]

        overall = sum(

            r.score

            for r in results

        ) / len(results)

        passed = overall >= 0.75

        retry = overall < 0.60

        reasons = [

            r.message

            for r in results

            if not r.passed

        ]

        return EvaluationResult(

            evaluations=results,

            overall_score=round(overall, 3),

            passed=passed,

            retry_recommended=retry,

            reasoning=reasons,

        )