"""
Jobs-To-Be-Done generation.

Responsibilities
----------------
• Generate structured JTBDs
• Separate functional, emotional and social jobs
• Link evidence to every job
• Produce confidence scores

No opportunity scoring or prioritization occurs here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .prompts import PROMPTS
from .schemas import (
    Evidence,
    ProblemStatement,
)


# ============================================================
# Models
# ============================================================


@dataclass(slots=True)
class JTBDItem:

    category: str

    actor: str

    situation: str

    motivation: str

    expected_outcome: str

    confidence: float

    supporting_evidence: list[str]


@dataclass(slots=True)
class JTBDResult:

    functional: JTBDItem

    emotional: JTBDItem

    social: JTBDItem

    assumptions: list[str]


# ============================================================
# LLM
# ============================================================


class JTBDGenerator:

    async def generate(
        self,
        problem: ProblemStatement,
        evidence: list[Evidence],
    ) -> JTBDResult:

        evidence_text = "\n".join(
            doc.content
            for doc in evidence
        )

        prompt = PROMPTS["jtbd"].render(
            problem=problem.statement,
            evidence=evidence_text,
        )

        #
        # TODO
        #
        # response = await llm.generate(prompt)
        # parse JSON
        #

        evidence_ids = [
            doc.id
            for doc in evidence[:3]
        ]

        return JTBDResult(

            functional=JTBDItem(

                category="functional",

                actor="Workspace Admin",

                situation="While onboarding a new workspace",

                motivation="Complete setup quickly",

                expected_outcome="Reach first value",

                confidence=0.90,

                supporting_evidence=evidence_ids,
            ),

            emotional=JTBDItem(

                category="emotional",

                actor="Workspace Admin",

                situation="During initial product setup",

                motivation="Feel confident that setup is correct",

                expected_outcome="Avoid frustration",

                confidence=0.82,

                supporting_evidence=evidence_ids,
            ),

            social=JTBDItem(

                category="social",

                actor="Workspace Admin",

                situation="Introducing the product to teammates",

                motivation="Appear competent",

                expected_outcome="Earn trust from colleagues",

                confidence=0.74,

                supporting_evidence=evidence_ids,
            ),

            assumptions=[
                "Current evidence sufficiently represents user motivation."
            ],
        )


# ============================================================
# Validator
# ============================================================


class JTBDValidator:

    def validate(
        self,
        jtbd: JTBDResult,
    ) -> list[str]:

        issues = []

        if jtbd.functional.confidence < 0.70:

            issues.append(
                "Low confidence functional JTBD."
            )

        if jtbd.emotional.confidence < 0.60:

            issues.append(
                "Emotional JTBD may require additional interviews."
            )

        if jtbd.social.confidence < 0.60:

            issues.append(
                "Social JTBD has weak evidence."
            )

        return issues


# ============================================================
# Public API
# ============================================================


class JTBDService:

    def __init__(self):

        self.generator = JTBDGenerator()

        self.validator = JTBDValidator()

    async def run(
        self,
        problem: ProblemStatement,
        evidence: list[Evidence],
    ) -> JTBDResult:

        result = await self.generator.generate(
            problem,
            evidence,
        )

        issues = self.validator.validate(result)

        result.assumptions.extend(issues)

        return result