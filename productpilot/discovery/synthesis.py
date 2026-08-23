"""Report and answer synthesis with hard monetary-incentive filtering."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from productpilot.discovery.schemas import (
    ChatAnswer,
    ClassifiedRecord,
    ConfidenceTier,
    EvidenceChunk,
    NormalizedRecord,
    OpportunityRecord,
)

MONETARY_TERMS = ("discount", "cashback", "coupon", "voucher", "promo")


class SafeSynthesisEngine:
    def render_report(self, opportunities: List[OpportunityRecord]) -> str:
        lines = ["# Myntra Wishlist Discovery Report", "", "## Ranked Opportunities", ""]
        for opportunity in opportunities:
            if self._contains_monetary_incentive(opportunity.description):
                continue
            lines.append("### {0}".format(opportunity.name))
            lines.append("- Description: {0}".format(opportunity.description))
            lines.append("- Evidence count: {0}".format(opportunity.evidence_count))
            lines.append("- Confidence tier: {0}".format(opportunity.confidence_tier.value))
            lines.append("- Sample excerpts: {0}".format(" | ".join(opportunity.sample_excerpts)))
            lines.append("")
        return "\n".join(lines)

    def answer_question(
        self,
        question: str,
        chunks: List[EvidenceChunk],
        classified_records: Optional[List[ClassifiedRecord]] = None,
    ) -> ChatAnswer:
        corpus = [record for record in (classified_records or []) if record.classification.is_relevant]
        if not chunks and not corpus:
            return ChatAnswer(
                answer_text="I could not find grounded evidence for that question in the current indexed corpus.",
                confidence_tier=ConfidenceTier.LOW,
                citations=[],
            )

        unique_chunks = self._dedupe_chunks(chunks)
        joined = " ".join(chunk.text for chunk in unique_chunks)
        out_of_scope_notice = None
        if self._contains_monetary_incentive(joined):
            out_of_scope_notice = (
                "Retrieved context mentions price-led behavior, but monetary incentives are explicitly out of scope for this system."
            )

        question_mode = self._question_mode(question)
        if corpus:
            answer_text, confidence, citations = self._answer_from_classified_corpus(
                question=question,
                question_mode=question_mode,
                records=corpus,
            )
        else:
            raw_chunks = [chunk for chunk in unique_chunks if chunk.chunk_type == "raw_evidence"]
            primary = raw_chunks[:3] if raw_chunks else unique_chunks[:3]
            summary_chunks = raw_chunks if raw_chunks else unique_chunks
            answer_text = self._build_concise_answer(question, summary_chunks)
            confidence = self._fallback_confidence(summary_chunks)
            citations = [
                {"url": chunk.source_url, "snippet": self._clean_snippet(chunk.text)}
                for chunk in primary
            ]
        return ChatAnswer(
            answer_text=answer_text,
            confidence_tier=confidence,
            citations=citations,
            out_of_scope_notice=out_of_scope_notice,
        )

    def _dedupe_chunks(self, chunks: List[EvidenceChunk]) -> List[EvidenceChunk]:
        unique: List[EvidenceChunk] = []
        seen = set()
        for chunk in chunks:
            dedup_key = NormalizedRecord.build_dedup_key(chunk.text)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            unique.append(chunk)
        return unique

    def _build_concise_answer(self, question: str, chunks: List[EvidenceChunk]) -> str:
        if not chunks:
            return "I could not find a concise grounded answer in the current indexed corpus."

        friction_counter: Counter[str] = Counter()
        intent_counter: Counter[str] = Counter()
        for chunk in chunks:
            metadata: Dict[str, object] = chunk.metadata or {}
            for friction in metadata.get("friction_type", []) or []:
                friction_counter[str(friction)] += 1
            intent = metadata.get("intent_signal")
            if intent:
                intent_counter[str(intent)] += 1

        unique_sources = len({chunk.source for chunk in chunks})
        evidence_count = len(chunks)
        top_friction = friction_counter.most_common(1)[0][0] if friction_counter else ""
        secondary_friction = friction_counter.most_common(2)[1][0] if len(friction_counter) > 1 else ""
        top_intent = intent_counter.most_common(1)[0][0] if intent_counter else ""

        summary_parts = []
        if top_friction:
            summary_parts.append(
                "Main takeaway: shoppers most often hesitate because of {0}.".format(
                    self._humanize_friction(top_friction)
                )
            )
        elif top_intent:
            summary_parts.append(
                "Main takeaway: shoppers are mostly using the wishlist as {0}.".format(
                    self._humanize_token(top_intent)
                )
            )
        else:
            summary_parts.append("Main takeaway: the evidence points to hesitation after saving items for later.")

        if secondary_friction and secondary_friction != top_friction:
            summary_parts.append(
                "A secondary theme is {0}.".format(self._humanize_friction(secondary_friction))
            )

        if top_intent == "bookmark":
            summary_parts.append("People are usually saving items to revisit later, then delaying the purchase.")

        summary_parts.append(
            "This is based on {0} unique evidence snippets across {1} sources.".format(
                evidence_count,
                unique_sources,
            )
        )
        return " ".join(summary_parts)

    def _answer_from_classified_corpus(
        self,
        question: str,
        question_mode: str,
        records: List[ClassifiedRecord],
    ) -> tuple[str, ConfidenceTier, List[Dict[str, str]]]:
        intent_counter: Counter[str] = Counter()
        friction_counter: Counter[str] = Counter()
        source_counter: Counter[str] = Counter()
        for record in records:
            intent_counter[record.classification.intent_signal.value] += 1
            source_counter[record.record.source.value] += 1
            for friction in record.classification.friction_type:
                friction_counter[friction.value] += 1

        source_count = len(source_counter)
        evidence_count = len(records)
        top_intent, top_intent_count = intent_counter.most_common(1)[0] if intent_counter else ("unclear", 0)
        top_friction, top_friction_count = friction_counter.most_common(1)[0] if friction_counter else ("other", 0)
        second_friction_count = friction_counter.most_common(2)[1][1] if len(friction_counter) > 1 else 0

        if question_mode == "wishlist_motivation":
            answer_text = self._wishlist_motivation_answer(
                top_intent=top_intent,
                top_intent_count=top_intent_count,
                intent_counter=intent_counter,
                friction_counter=friction_counter,
                evidence_count=evidence_count,
                source_count=source_count,
            )
            confidence = (
                ConfidenceTier.MEDIUM if evidence_count >= 25 and source_count >= 4 else ConfidenceTier.LOW
            )
            citations = self._select_record_citations(
                records,
                preferred_frictions=["comparison_paralysis", "price_timing", "fit_size_doubt"],
            )
            return answer_text, confidence, citations

        if question_mode == "top_friction":
            answer_text = (
                "Top friction: {0}. It appears most often in the cleaned corpus, ahead of the next blocker category. "
                "In practice, users save items but do not purchase because they still feel uncertain at decision time."
            ).format(self._humanize_friction(top_friction))
            confidence = (
                ConfidenceTier.HIGH
                if top_friction_count >= second_friction_count + 5 and source_count >= 4
                else ConfidenceTier.MEDIUM
                if top_friction_count >= 5 and source_count >= 3
                else ConfidenceTier.LOW
            )
            citations = self._select_record_citations(records, preferred_frictions=[top_friction])
            return answer_text, confidence, citations

        if question_mode == "conversion_blocker":
            answer_text = (
                "Main conversion blocker: {0}. Users are not treating the wishlist as a near-checkout queue; "
                "they usually save items, revisit them later, and then stall when the product still feels uncertain."
            ).format(self._humanize_friction(top_friction))
            if friction_counter.get("review_gap", 0) >= 4:
                answer_text += " Lack of enough reviews or real-life photos is another recurring blocker."
            confidence = (
                ConfidenceTier.MEDIUM if top_friction_count >= 6 and source_count >= 3 else ConfidenceTier.LOW
            )
            citations = self._select_record_citations(records, preferred_frictions=[top_friction, "review_gap"])
            return answer_text, confidence, citations

        relevant_chunks = [
            EvidenceChunk(
                chunk_id="raw:{0}".format(record.record.content_hash),
                chunk_type="raw_evidence",
                source=record.record.source.value,
                source_url=record.record.url,
                text=record.classification.excerpt,
                metadata={
                    "intent_signal": record.classification.intent_signal.value,
                    "friction_type": [item.value for item in record.classification.friction_type],
                },
            )
            for record in records[:12]
        ]
        answer_text = self._build_concise_answer(question, relevant_chunks)
        confidence = self._fallback_confidence(relevant_chunks)
        citations = self._select_record_citations(records)
        return answer_text, confidence, citations

    def _wishlist_motivation_answer(
        self,
        top_intent: str,
        top_intent_count: int,
        intent_counter: Counter[str],
        friction_counter: Counter[str],
        evidence_count: int,
        source_count: int,
    ) -> str:
        share = round((top_intent_count / evidence_count) * 100) if evidence_count else 0
        parts = []
        if top_intent == "bookmark":
            parts.append(
                "Users mostly add fashion items to their wishlist as a personal shortlist, not as an immediate buy signal."
            )
        elif top_intent == "price_watch":
            parts.append(
                "Users mostly add fashion items to their wishlist to watch timing and come back later when they feel ready to buy."
            )
        else:
            parts.append("Users mostly add fashion items to their wishlist to defer the final decision and revisit options later.")

        if friction_counter.get("comparison_paralysis", 0) >= 4:
            parts.append("A common reason is wanting to compare multiple options before choosing one.")
        if friction_counter.get("fit_size_doubt", 0) >= 4:
            parts.append("Another common reason is that they are not yet confident about fit, size, or product details.")
        if intent_counter.get("price_watch", 0) >= 2:
            parts.append("A smaller segment also uses the wishlist to keep an eye on timing or price.")

        parts.append(
            "In this cleaned corpus, that dominant behavior shows up in about {0}% of relevant records across {1} sources.".format(
                share,
                source_count,
            )
        )
        return " ".join(parts)

    def _select_record_citations(
        self,
        records: List[ClassifiedRecord],
        preferred_frictions: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        selected: List[ClassifiedRecord] = []
        used_urls = set()
        preferred_frictions = preferred_frictions or []

        for friction in preferred_frictions:
            for record in records:
                friction_values = [item.value for item in record.classification.friction_type]
                if friction in friction_values and record.record.url not in used_urls:
                    selected.append(record)
                    used_urls.add(record.record.url)
                    break

        for record in records:
            if len(selected) >= 3:
                break
            if record.record.url in used_urls:
                continue
            selected.append(record)
            used_urls.add(record.record.url)

        return [
            {
                "url": record.record.url,
                "snippet": self._clean_snippet(record.classification.excerpt),
            }
            for record in selected[:3]
        ]

    def _question_mode(self, question: str) -> str:
        lowered = question.lower()
        if any(phrase in lowered for phrase in ["top friction", "biggest friction", "main friction", "top blocker"]):
            return "top_friction"
        if any(phrase in lowered for phrase in ["not converting", "not convert", "why don't", "why do shoppers not buy", "why are shoppers not buying", "why no purchase"]):
            return "conversion_blocker"
        if any(phrase in lowered for phrase in ["why do users add", "why add", "why do users save", "why save", "why wishlist"]):
            return "wishlist_motivation"
        return "general"

    def _fallback_confidence(self, chunks: List[EvidenceChunk]) -> ConfidenceTier:
        source_count = len({chunk.source for chunk in chunks})
        evidence_count = len(chunks)
        if source_count >= 4 and evidence_count >= 8:
            return ConfidenceTier.MEDIUM
        if source_count >= 2 and evidence_count >= 3:
            return ConfidenceTier.LOW
        return ConfidenceTier.LOW

    def _clean_snippet(self, text: str) -> str:
        cleaned = NormalizedRecord.canonicalize_text(text)
        if len(cleaned) <= 160:
            return cleaned
        return cleaned[:157] + "..."

    def _humanize_friction(self, friction: str) -> str:
        mapping = {
            "fit_size_doubt": "fit and size uncertainty",
            "styling_uncertainty": "uncertainty about styling or outfit matching",
            "price_timing": "waiting for the right price or timing",
            "review_gap": "not having enough trustworthy reviews or photos",
            "occasion_mismatch": "uncertainty about the right occasion to use the item",
            "social_validation": "wanting outside validation before buying",
            "forgotten_lost_in_list": "items getting lost in an overcrowded wishlist",
            "comparison_paralysis": "comparison overload across too many options",
            "other": "general uncertainty after saving items",
        }
        return mapping.get(friction, self._humanize_token(friction))

    def _humanize_token(self, value: str) -> str:
        return value.replace("_", " ")

    def _contains_monetary_incentive(self, text: str) -> bool:
        lowered = text.lower()
        return any(term in lowered for term in MONETARY_TERMS)
