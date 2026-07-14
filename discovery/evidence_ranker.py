"""
Evidence ranking for the ProductPilot Discovery Agent.

Responsibilities
----------------
• Re-rank retrieved evidence
• Compute composite evidence scores
• Filter low-quality evidence
• Diversify evidence sources
• Produce ranked Evidence objects

This module performs NO reasoning.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .config import settings
from .schemas import Evidence


# ============================================================
# Composite Score
# ============================================================


class CompositeScorer:
    """
    Computes a weighted evidence score.
    """

    def score(self, evidence: Evidence) -> float:

        weights = settings.ranking

        return (
            evidence.relevance * weights.weight_relevance
            + evidence.confidence * weights.weight_confidence
            + evidence.freshness * weights.weight_freshness
            + evidence.trust * weights.weight_trust
        )


# ============================================================
# Filters
# ============================================================


class EvidenceFilter:
    """
    Removes weak evidence.
    """

    def filter(
        self,
        evidence: Iterable[Evidence],
    ) -> list[Evidence]:

        minimum = settings.retrieval.min_relevance_score

        return [
            e
            for e in evidence
            if e.relevance >= minimum
        ]


# ============================================================
# Diversity
# ============================================================


class DiversitySelector:
    """
    Prevents all returned evidence from coming
    from the same source type.
    """

    def diversify(
        self,
        evidence: list[Evidence],
    ) -> list[Evidence]:

        grouped: dict[str, list[Evidence]] = defaultdict(list)

        for item in evidence:
            grouped[item.source_type].append(item)

        diversified: list[Evidence] = []

        # Round-robin selection
        while grouped:

            empty = []

            for source, docs in grouped.items():

                if docs:

                    diversified.append(docs.pop(0))

                if not docs:
                    empty.append(source)

            for source in empty:
                grouped.pop(source)

        return diversified


# ============================================================
# Ranker
# ============================================================


class EvidenceRanker:

    def __init__(self):

        self.scorer = CompositeScorer()

        self.filter = EvidenceFilter()

        self.diversity = DiversitySelector()

    def rank(
        self,
        evidence: list[Evidence],
    ) -> list[Evidence]:

        evidence = self.filter.filter(evidence)

        evidence.sort(
            key=self.scorer.score,
            reverse=True,
        )

        evidence = self.diversity.diversify(evidence)

        return evidence


# ============================================================
# Diagnostics
# ============================================================


class RankingStatistics:

    @staticmethod
    def summarize(
        evidence: list[Evidence],
    ) -> dict:

        if not evidence:

            return {
                "documents": 0,
                "average_score": 0,
                "source_types": {},
            }

        scorer = CompositeScorer()

        scores = [
            scorer.score(e)
            for e in evidence
        ]

        source_counts: dict[str, int] = defaultdict(int)

        for doc in evidence:

            source_counts[str(doc.source_type)] += 1

        return {

            "documents": len(evidence),

            "average_score": round(
                sum(scores) / len(scores),
                3,
            ),

            "highest_score": round(
                max(scores),
                3,
            ),

            "lowest_score": round(
                min(scores),
                3,
            ),

            "source_distribution": dict(source_counts),
        }