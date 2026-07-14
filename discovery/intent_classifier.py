"""
Intent classification for the ProductPilot Discovery Agent.

Responsibilities
----------------
• Determine the primary discovery intent.
• Combine rule-based and LLM-based classification.
• Return confidence and reasoning.
• Never perform retrieval or reasoning.

Python 3.12+
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .prompts import PROMPTS
from .schemas import DiscoveryRequest
from .types import DiscoveryIntent


# ============================================================
# Result
# ============================================================


@dataclass(slots=True)
class IntentResult:

    intent: DiscoveryIntent

    confidence: float

    reasoning: str

    method: str


# ============================================================
# Keyword Rules
# ============================================================


RULES: dict[DiscoveryIntent, Sequence[str]] = {

    DiscoveryIntent.BUG: [
        "bug",
        "broken",
        "crash",
        "exception",
        "fails",
        "failure",
        "error",
    ],

    DiscoveryIntent.PERFORMANCE: [
        "slow",
        "latency",
        "lag",
        "loading",
        "performance",
        "freeze",
    ],

    DiscoveryIntent.ACTIVATION: [
        "activation",
        "onboarding",
        "first value",
        "signup",
        "invite",
    ],

    DiscoveryIntent.RETENTION: [
        "retention",
        "renewal",
        "churn",
        "return",
    ],

    DiscoveryIntent.ENGAGEMENT: [
        "engagement",
        "usage",
        "adoption",
        "daily active",
    ],

    DiscoveryIntent.REVENUE: [
        "pricing",
        "revenue",
        "upsell",
        "conversion",
        "trial",
    ],

    DiscoveryIntent.PLATFORM: [
        "api",
        "sdk",
        "developer",
        "integration",
        "platform",
    ],

    DiscoveryIntent.UX: [
        "confusing",
        "difficult",
        "ux",
        "ui",
        "navigation",
    ],

    DiscoveryIntent.RESEARCH: [
        "explore",
        "research",
        "validate",
        "learn",
        "unknown",
    ],

}


# ============================================================
# Rule Engine
# ============================================================


class RuleClassifier:

    def classify(
        self,
        text: str,
    ) -> IntentResult | None:

        text = text.lower()

        best_intent = None
        best_score = 0

        for intent, keywords in RULES.items():

            score = sum(
                keyword in text
                for keyword in keywords
            )

            if score > best_score:

                best_score = score
                best_intent = intent

        if best_intent is None:

            return None

        confidence = min(
            0.95,
            0.55 + best_score * 0.1,
        )

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            reasoning="Matched rule-based keywords.",
            method="rules",
        )


# ============================================================
# LLM Classifier
# ============================================================


class LLMClassifier:
    """
    Wrapper around an LLM provider.

    Currently returns UNKNOWN until integrated.
    """

    async def classify(
        self,
        text: str,
    ) -> IntentResult:

        prompt = PROMPTS["intent"].render(
            input=text,
        )

        #
        # TODO
        #
        # response = await llm.generate(...)
        #
        # parse JSON
        #
        # return IntentResult(...)
        #

        return IntentResult(
            intent=DiscoveryIntent.UNKNOWN,
            confidence=0.50,
            reasoning="LLM integration pending.",
            method="llm",
        )


# ============================================================
# Hybrid Classifier
# ============================================================


class IntentClassifier:

    def __init__(self):

        self.rules = RuleClassifier()

        self.llm = LLMClassifier()

    async def classify(
        self,
        request: DiscoveryRequest,
    ) -> IntentResult:

        text = self._build_input(request)

        rule_result = self.rules.classify(text)

        #
        # High confidence rule
        #

        if (
            rule_result
            and rule_result.confidence >= 0.80
        ):

            return rule_result

        #
        # Otherwise ask the LLM
        #

        llm_result = await self.llm.classify(text)

        #
        # If LLM is uncertain,
        # fall back to rules.
        #

        if (
            rule_result
            and llm_result.confidence < 0.70
        ):

            return rule_result

        return llm_result

    def _build_input(
        self,
        request: DiscoveryRequest,
    ) -> str:

        parts = [

            request.user_intent.goal,

            request.user_intent.feedback_summary,

            request.user_intent.analytics_problem,

            request.user_intent.business_goal,

            request.company_context.strategy_summary,

            request.retrieval_context.source_notes,

        ]

        return "\n".join(
            p
            for p in parts
            if p
        )