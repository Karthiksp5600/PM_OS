from datetime import datetime

from productpilot.discovery.aggregation import OpportunityAggregator
from productpilot.discovery.schemas import (
    ClassificationResult,
    ClassifiedRecord,
    FrictionType,
    IntentSignal,
    NormalizedRecord,
    SegmentHints,
    SourceName,
)


def _classified_record(content_hash: str, friction: FrictionType, source: SourceName) -> ClassifiedRecord:
    return ClassifiedRecord(
        record=NormalizedRecord(
            source=source,
            url="https://example.com/{0}".format(content_hash),
            author_id_hash="author",
            timestamp=datetime(2026, 8, 24),
            text="sample text {0}".format(content_hash),
            content_hash=content_hash,
        ),
        classification=ClassificationResult(
            is_relevant=True,
            intent_signal=IntentSignal.BOOKMARK,
            friction_type=[friction],
            comparison_behavior=False,
            off_platform_research=[],
            segment_hints=SegmentHints(),
            confidence=0.9,
            excerpt="excerpt {0}".format(content_hash),
        ),
    )


def test_other_opportunities_rank_last():
    aggregator = OpportunityAggregator()
    records = [
        _classified_record("other-1", FrictionType.OTHER, SourceName.REDDIT),
        _classified_record("other-2", FrictionType.OTHER, SourceName.PLAY_STORE),
        _classified_record("other-3", FrictionType.OTHER, SourceName.DUCKDUCKGO),
        _classified_record("fit-1", FrictionType.FIT_SIZE_DOUBT, SourceName.REDDIT),
    ]

    opportunities = aggregator.build_opportunities(records)

    assert opportunities[0].name.startswith("fit_size_doubt:")
    assert opportunities[-1].name.startswith("other:")


def test_unclear_opportunities_rank_last():
    aggregator = OpportunityAggregator()
    clear_record = ClassifiedRecord(
        record=NormalizedRecord(
            source=SourceName.REDDIT,
            url="https://example.com/clear",
            author_id_hash="author",
            timestamp=datetime(2026, 8, 24),
            text="clear sample",
            content_hash="clear",
        ),
        classification=ClassificationResult(
            is_relevant=True,
            intent_signal=IntentSignal.BOOKMARK,
            friction_type=[FrictionType.FIT_SIZE_DOUBT],
            comparison_behavior=False,
            off_platform_research=[],
            segment_hints=SegmentHints(),
            confidence=0.9,
            excerpt="clear excerpt",
        ),
    )
    unclear_record = ClassifiedRecord(
        record=NormalizedRecord(
            source=SourceName.PLAY_STORE,
            url="https://example.com/unclear",
            author_id_hash="author",
            timestamp=datetime(2026, 8, 24),
            text="unclear sample",
            content_hash="unclear",
        ),
        classification=ClassificationResult(
            is_relevant=True,
            intent_signal=IntentSignal.UNCLEAR,
            friction_type=[FrictionType.FIT_SIZE_DOUBT],
            comparison_behavior=False,
            off_platform_research=[],
            segment_hints=SegmentHints(),
            confidence=0.9,
            excerpt="unclear excerpt",
        ),
    )

    opportunities = aggregator.build_opportunities([unclear_record, clear_record])

    assert opportunities[0].name.endswith(":bookmark")
    assert opportunities[-1].name.endswith(":unclear")
