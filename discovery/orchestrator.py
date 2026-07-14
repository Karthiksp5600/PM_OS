"""
Discovery Workflow Orchestrator.

Coordinates the complete Discovery pipeline.

Responsibilities
----------------
• Execute stages
• Maintain execution context
• Retry failed stages
• Collect metrics
• Trigger evaluations
• Produce Discovery Artifact
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .evaluator import (
    DiscoveryEvaluator,
    EvaluationContext,
)
from .evidence_ranker import EvidenceRanker
from .hypothesis_generator import HypothesisService
from .intent_classifier import IntentClassifier
from .jtbd import JTBDService
from .metrics import MetricsCollector
from .opportunity_scorer import OpportunityScorer
from .problem_extractor import ProblemExtractor
from .retriever import create_retriever
from .schemas import DiscoveryRequest


# =====================================================
# Stage Enum
# =====================================================


class Stage(str, Enum):

    INTENT = "intent"

    RETRIEVAL = "retrieval"

    RANKING = "ranking"

    PROBLEM = "problem"

    JTBD = "jtbd"

    HYPOTHESIS = "hypothesis"

    OPPORTUNITY = "opportunity"

    EVALUATION = "evaluation"

    METRICS = "metrics"


# =====================================================
# Pipeline Context
# =====================================================


@dataclass(slots=True)
class PipelineContext:

    request: DiscoveryRequest

    intent: Any | None = None

    evidence: list[Any] = field(default_factory=list)

    problem: Any | None = None

    jtbd: Any | None = None

    hypotheses: Any | None = None

    opportunity: Any | None = None

    evaluation: Any | None = None

    metrics: Any | None = None


# =====================================================
# Base Stage
# =====================================================


class PipelineStage:

    name: Stage

    async def execute(
        self,
        context: PipelineContext,
    ):
        raise NotImplementedError


# =====================================================
# Intent
# =====================================================


class IntentStage(PipelineStage):

    name = Stage.INTENT

    def __init__(self):

        self.classifier = IntentClassifier()

    async def execute(
        self,
        context,
    ):

        context.intent = await self.classifier.classify(
            context.request
        )


# =====================================================
# Retrieval
# =====================================================


class RetrievalStage(PipelineStage):

    name = Stage.RETRIEVAL

    def __init__(self):

        self.retriever = create_retriever()

    async def execute(
        self,
        context,
    ):

        goal = (

            context.request.user_intent.goal

            or context.request.user_intent.feedback_summary

            or ""

        )

        notes = (
            context.request
            .retrieval_context
            .source_notes
        )

        context.evidence = await self.retriever.retrieve(

            goal=goal,

            context=notes,

        )


# =====================================================
# Rank
# =====================================================


class RankingStage(PipelineStage):

    name = Stage.RANKING

    def __init__(self):

        self.ranker = EvidenceRanker()

    async def execute(
        self,
        context,
    ):

        context.evidence = self.ranker.rank(
            context.evidence
        )


# =====================================================
# Problem
# =====================================================


class ProblemStage(PipelineStage):

    name = Stage.PROBLEM

    def __init__(self):

        self.extractor = ProblemExtractor()

    async def execute(
        self,
        context,
    ):

        context.problem = await self.extractor.extract(

            context.request,

            context.evidence,

        )


# =====================================================
# JTBD
# =====================================================


class JTBDStage(PipelineStage):

    name = Stage.JTBD

    def __init__(self):

        self.service = JTBDService()

    async def execute(
        self,
        context,
    ):

        context.jtbd = await self.service.run(

            context.problem.problem,

            context.evidence,

        )


# =====================================================
# Hypothesis
# =====================================================


class HypothesisStage(PipelineStage):

    name = Stage.HYPOTHESIS

    def __init__(self):

        self.service = HypothesisService()

    async def execute(
        self,
        context,
    ):

        context.hypotheses = await self.service.run(

            context.problem.problem,

            context.evidence,

        )


# =====================================================
# Opportunity
# =====================================================


class OpportunityStage(PipelineStage):

    name = Stage.OPPORTUNITY

    def __init__(self):

        self.scorer = OpportunityScorer()

    async def execute(
        self,
        context,
    ):

        context.opportunity = self.scorer.score(

            context.problem,

            context.evidence,

            context.hypotheses,

        )


# =====================================================
# Evaluation
# =====================================================


class EvaluationStage(PipelineStage):

    name = Stage.EVALUATION

    def __init__(self):

        self.evaluator = DiscoveryEvaluator()

    async def execute(
        self,
        context,
    ):

        eval_context = EvaluationContext(

            problem=context.problem,

            evidence=context.evidence,

            jtbd=context.jtbd,

            hypotheses=context.hypotheses,

            opportunity=context.opportunity,

        )

        context.evaluation = self.evaluator.evaluate(
            eval_context
        )


# =====================================================
# Metrics
# =====================================================


class MetricsStage(PipelineStage):

    name = Stage.METRICS

    def __init__(self):

        self.collector = MetricsCollector()

    async def execute(
        self,
        context,
    ):

        context.metrics = self.collector.collect(

            prompt="",

            response="",

            evidence=context.evidence,

            problem=context.problem,

            hypotheses=context.hypotheses,

            opportunity=context.opportunity,

            evaluation=context.evaluation,

        )


# =====================================================
# Orchestrator
# =====================================================


class DiscoveryWorkflow:

    def __init__(self):

        self.pipeline = [

            IntentStage(),

            RetrievalStage(),

            RankingStage(),

            ProblemStage(),

            JTBDStage(),

            HypothesisStage(),

            OpportunityStage(),

            EvaluationStage(),

            MetricsStage(),

        ]

    async def run(

        self,

        request: DiscoveryRequest,

    ) -> PipelineContext:

        context = PipelineContext(
            request=request
        )

        for stage in self.pipeline:

            await stage.execute(
                context
            )

        return context