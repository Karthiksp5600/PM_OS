from pathlib import Path

from productpilot.discovery.service import DiscoveryEngineService


BASE_DIR = Path(__file__).resolve().parents[2]


def test_vertical_slice_end_to_end():
    service = DiscoveryEngineService(BASE_DIR)

    ingest_stats = service.ingest()
    assert ingest_stats["total_records"] == 70
    assert ingest_stats["source_count"] == 7
    assert ingest_stats["cleaned_records"] == 70

    classified_count = service.classify()
    assert classified_count >= 1

    aggregate_stats = service.aggregate()
    assert aggregate_stats["opportunity_count"] >= 1

    dashboard_stats = service.dashboard_stats()
    assert dashboard_stats["source_count"] == 7
    assert dashboard_stats["cleaned_records"] == 70
    assert dashboard_stats["relevant_records"] >= 1

    answer = service.answer("What is the top friction point for footwear under ₹2000?")
    assert answer["citations"]
    assert "confidence_tier" in answer
