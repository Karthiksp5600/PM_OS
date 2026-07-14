"""
Prompt templates for the ProductPilot Discovery Agent.

This module centralizes all prompts used by the Discovery pipeline.

Guidelines:
- No business logic
- Versioned prompts
- Easy A/B testing
- Easy replacement
"""

from __future__ import annotations

from dataclasses import dataclass
from string import Template


# ==========================================================
# Prompt Template
# ==========================================================

@dataclass(frozen=True)
class Prompt:

    name: str

    version: str

    system: str

    user: Template

    def render(self, **kwargs) -> str:
        return self.user.safe_substitute(**kwargs)


# ==========================================================
# Shared System Prompt
# ==========================================================

DISCOVERY_SYSTEM = """
You are a Senior Product Manager responsible for product discovery.

Your job is NOT to invent features.

Your responsibilities are:

• Understand the underlying problem.
• Separate symptoms from root causes.
• Ground every claim in evidence.
• Never fabricate evidence.
• Clearly distinguish assumptions from facts.
• Highlight missing information.
• Produce structured reasoning.

Always think like a senior PM.
Return structured JSON only.
"""


# ==========================================================
# Intent Classification
# ==========================================================

INTENT_CLASSIFIER = Prompt(
    name="intent_classifier",
    version="v1",
    system=DISCOVERY_SYSTEM,
    user=Template(
        """
Classify the following product request.

Request

$input

Choose ONE intent:

- Growth
- Retention
- Engagement
- Revenue
- Activation
- Platform
- UX
- Bug
- Performance
- Compliance
- Research
- Internal Tool

Return JSON:

{
  "intent":"",
  "confidence":0.0,
  "reason":""
}
"""
    ),
)


# ==========================================================
# Problem Extraction
# ==========================================================

PROBLEM_EXTRACTOR = Prompt(
    name="problem_extractor",
    version="v1",
    system=DISCOVERY_SYSTEM,
    user=Template(
        """
Business Goal

$goal

Customer Evidence

$evidence

Extract:

- User Problem
- Business Problem
- Desired Outcome
- Constraints
- Risks

Return JSON only.
"""
    ),
)


# ==========================================================
# JTBD
# ==========================================================

JTBD_PROMPT = Prompt(
    name="jtbd",
    version="v1",
    system=DISCOVERY_SYSTEM,
    user=Template(
        """
Problem

$problem

Evidence

$evidence

Generate ONE Jobs-To-Be-Done statement.

Return JSON:

{
 "actor":"",
 "situation":"",
 "motivation":"",
 "expected_outcome":""
}
"""
    ),
)


# ==========================================================
# Root Cause Hypothesis
# ==========================================================

ROOT_CAUSE_PROMPT = Prompt(
    name="root_cause",
    version="v1",
    system=DISCOVERY_SYSTEM,
    user=Template(
        """
Problem

$problem

Evidence

$evidence

Generate 3 competing hypotheses.

For each provide:

- hypothesis
- confidence
- supporting evidence
- assumptions

Return JSON only.
"""
    ),
)


# ==========================================================
# Opportunity Scoring
# ==========================================================

OPPORTUNITY_PROMPT = Prompt(
    name="opportunity",
    version="v1",
    system=DISCOVERY_SYSTEM,
    user=Template(
        """
Problem

$problem

Business Context

$context

Estimate

- Reach
- Severity
- Frequency
- Strategic Alignment
- Revenue Impact
- Retention Impact
- Risk

Return JSON only.
"""
    ),
)


# ==========================================================
# Discovery Report
# ==========================================================

DISCOVERY_REPORT = Prompt(
    name="discovery_report",
    version="v1",
    system=DISCOVERY_SYSTEM,
    user=Template(
        """
Create the final Discovery Report.

Inputs

Problem

$problem

Evidence

$evidence

JTBD

$jtbd

Hypotheses

$hypotheses

Opportunity

$opportunity

Generate

- Problem Statement
- Why Now
- Scope
- Assumptions
- Open Questions
- Success Definition

Return JSON only.
"""
    ),
)


# ==========================================================
# AI Evaluation
# ==========================================================

DISCOVERY_EVAL = Prompt(
    name="discovery_eval",
    version="v1",
    system=DISCOVERY_SYSTEM,
    user=Template(
        """
Evaluate this discovery report.

Report

$report

Evaluate:

- Evidence Coverage
- Completeness
- Hallucination Risk
- Business Logic
- KPI Readiness
- Citation Quality

Return

{
 "overall_score":0.0,
 "passed":true,
 "issues":[]
}
"""
    ),
)


# ==========================================================
# Prompt Registry
# ==========================================================

PROMPTS = {
    "intent": INTENT_CLASSIFIER,
    "problem": PROBLEM_EXTRACTOR,
    "jtbd": JTBD_PROMPT,
    "hypothesis": ROOT_CAUSE_PROMPT,
    "opportunity": OPPORTUNITY_PROMPT,
    "report": DISCOVERY_REPORT,
    "evaluation": DISCOVERY_EVAL,
}