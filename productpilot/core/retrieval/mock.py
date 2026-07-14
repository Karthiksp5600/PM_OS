"""Mock retrieval provider for testing.
"""

from __future__ import annotations

from typing import Any, Sequence

from ..models import Evidence
from ..types import SourceType
from .base import RetrievalProvider


class MockRetriever(RetrievalProvider):
    """Simulates a retrieval vector database by returning fixed test Evidence documents."""

    async def retrieve(self, query: str, top_k: int, **kwargs: Any) -> Sequence[Evidence]:
        return [
            Evidence(
                id="doc_001",
                title="Customer Interview",
                content="Workspace admins struggle during onboarding.",
                source_type=SourceType.INTERVIEW,
                confidence=0.92,
                relevance=0.94,
                freshness=0.90,
                trust=0.95,
                metadata={"query": query},
            ),
            Evidence(
                id="doc_002",
                title="Analytics",
                content="Drop-off occurs before invite teammates.",
                source_type=SourceType.ANALYTICS,
                confidence=0.90,
                relevance=0.91,
                freshness=0.98,
                trust=0.99,
                metadata={},
            ),
        ]
