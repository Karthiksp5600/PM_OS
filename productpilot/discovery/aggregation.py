"""Deterministic aggregation and opportunity scoring."""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple

from productpilot.discovery.schemas import (
    ClassifiedRecord,
    ConfidenceTier,
    EvidenceChunk,
    FrictionType,
    OpportunityRecord,
)


MONETARY_TERMS = ("discount", "cashback", "coupon", "promo", "sale", "markdown")


class OpportunityAggregator:
    def build_opportunities(self, records: List[ClassifiedRecord]) -> List[OpportunityRecord]:
        grouped: DefaultDict[Tuple[str, str], List[ClassifiedRecord]] = defaultdict(list)
        for record in records:
            if not record.classification.is_relevant:
                continue
            for friction in record.classification.friction_type:
                grouped[(friction.value, record.classification.intent_signal.value)].append(record)

        opportunities: List[OpportunityRecord] = []
        for (friction, intent), group in grouped.items():
            source_count = len({item.record.source for item in group})
            confidence_tier = (
                ConfidenceTier.HIGH if source_count >= 2 and len(group) >= 3 else
                ConfidenceTier.MEDIUM if source_count >= 1 and len(group) >= 2 else
                ConfidenceTier.LOW
            )
            name = f"{friction}:{intent}"
            description = self._describe(friction, intent, len(group))
            if self._contains_monetary_incentive(description):
                continue
            opportunities.append(
                OpportunityRecord(
                    name=name,
                    description=description,
                    evidence_count=len(group),
                    sample_excerpts=[item.classification.excerpt for item in group[:3]],
                    segments_affected=[],
                    confidence_tier=confidence_tier,
                    source_count=source_count,
                    friction_types=[FrictionType(friction)],
                    intent_signals=[group[0].classification.intent_signal],
                )
            )
        return sorted(opportunities, key=lambda item: (item.evidence_count, item.source_count), reverse=True)

    def build_evidence_chunks(self, records: List[ClassifiedRecord], opportunities: List[OpportunityRecord]) -> List[EvidenceChunk]:
        chunks: List[EvidenceChunk] = []
        for record in records:
            chunks.append(
                EvidenceChunk(
                    chunk_id="raw:{0}".format(record.record.content_hash),
                    chunk_type="raw_evidence",
                    source=record.record.source.value,
                    source_url=record.record.url,
                    text=record.classification.excerpt,
                    metadata={
                        "intent_signal": record.classification.intent_signal.value,
                        "friction_type": [item.value for item in record.classification.friction_type],
                        "category": record.classification.segment_hints.category,
                        "price_tier": record.classification.segment_hints.price_tier,
                        "user_type": record.classification.segment_hints.user_type,
                    },
                )
            )
        for opportunity in opportunities:
            chunks.append(
                EvidenceChunk(
                    chunk_id="opportunity:{0}".format(opportunity.name),
                    chunk_type="synthesized_insight",
                    source="aggregation",
                    source_url="opportunities.json",
                    text=opportunity.description,
                    metadata={
                        "confidence_tier": opportunity.confidence_tier.value,
                        "segments_affected": opportunity.segments_affected,
                        "evidence_count": opportunity.evidence_count,
                    },
                )
            )
        return chunks

    def _describe(self, friction: str, intent: str, evidence_count: int) -> str:
        return (
            "Users treating wishlist items as {0} often stall because of {1}. "
            "This pattern appears in {2} evidence snippets across the current corpus."
        ).format(intent.replace("_", " "), friction.replace("_", " "), evidence_count)

    def _contains_monetary_incentive(self, text: str) -> bool:
        lowered = text.lower()
        return any(term in lowered for term in MONETARY_TERMS)
