"""Base retrieval interfaces and orchestrator for ProductPilot.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from ..models import Evidence
from ..utils import deduplicate_by_key


class RetrievalProvider(ABC):
    """Abstract base class for specific retrieval backends (e.g. Pinecone, Chroma)."""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int, **kwargs: Any) -> Sequence[Evidence]:
        """Retrieve relevant Evidence from the vector store or index."""
        pass


class QueryBuilder:
    """Helper to convert structured agent requests into plain-text search queries."""

    def build(self, primary_input: str, context_notes: str | None = None) -> str:
        if context_notes:
            return f"{primary_input}\n\n{context_notes}"
        return primary_input


class Retriever:
    """Main retrieval interface exposed to agents.

    Delegates to a registered RetrievalProvider, then normalizes, deduplicates,
    and sorts the results by relevance and confidence.
    """

    def __init__(self, provider: RetrievalProvider) -> None:
        self.provider = provider
        self.query_builder = QueryBuilder()

    async def retrieve(
        self,
        *,
        goal: str,
        context: str | None = None,
        top_k: int = 10,
        **kwargs: Any,
    ) -> list[Evidence]:
        query = self.query_builder.build(goal, context)
        documents = await self.provider.retrieve(query=query, top_k=top_k, **kwargs)

        # Deduplicate evidence by unique ID
        deduped = deduplicate_by_key(list(documents), "id")

        # Sort descending by relevance, then confidence
        return sorted(
            deduped,
            key=lambda d: (d.relevance, d.confidence),
            reverse=True,
        )
