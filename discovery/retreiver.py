"""
Evidence retrieval layer for ProductPilot.

Responsibilities
----------------
• Build retrieval queries
• Retrieve from one or more knowledge sources
• Normalize documents
• Deduplicate evidence
• Return strongly typed Evidence objects

Business logic such as ranking or reasoning does NOT belong here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from .config import settings
from .logger import logger
from .schemas import Evidence
from .types import SourceType
from .utils import deduplicate_by_key


# ============================================================
# Abstract Provider
# ============================================================


class RetrievalProvider(ABC):
    """
    Base class for every retrieval backend.
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int,
    ) -> Sequence[Evidence]:
        pass


# ============================================================
# Mock Provider
# ============================================================


class MockRetriever(RetrievalProvider):
    """
    Temporary implementation.

    Replace with Pinecone, Chroma, etc.
    """

    async def retrieve(
        self,
        query: str,
        top_k: int,
    ) -> Sequence[Evidence]:

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
                metadata={
                    "query": query
                },
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


# ============================================================
# Query Builder
# ============================================================


class QueryBuilder:
    """
    Converts discovery requests into retrieval queries.
    """

    def build(
        self,
        goal: str,
        context: str | None = None,
    ) -> str:

        if context:
            return f"{goal}\n\n{context}"

        return goal


# ============================================================
# Retriever
# ============================================================


class Retriever:
    """
    Main retrieval interface used by Discovery.
    """

    def __init__(
        self,
        provider: RetrievalProvider,
    ):

        self.provider = provider

        self.query_builder = QueryBuilder()

    async def retrieve(
        self,
        *,
        goal: str,
        context: str | None = None,
    ) -> list[Evidence]:

        query = self.query_builder.build(
            goal,
            context,
        )

        logger.info(
            "Running retrieval",
            extra={
                "query": query,
            },
        )

        documents = await self.provider.retrieve(
            query=query,
            top_k=settings.retrieval.top_k,
        )

        documents = deduplicate_by_key(
            list(documents),
            "id",
        )

        return sorted(
            documents,
            key=lambda d: (
                d.relevance,
                d.confidence,
            ),
            reverse=True,
        )


# ============================================================
# Factory
# ============================================================


def create_retriever() -> Retriever:
    """
    Temporary factory.

    Later this becomes:

    if provider == pinecone
    if provider == chroma
    if provider == weaviate
    ...
    """

    provider = MockRetriever()

    return Retriever(provider)