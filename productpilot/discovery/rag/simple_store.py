"""Simple local retrieval store for the vertical slice."""

from __future__ import annotations

import re
from typing import List, Tuple

from productpilot.discovery.schemas import EvidenceChunk


class LocalRAGStore:
    def __init__(self) -> None:
        self._chunks: List[EvidenceChunk] = []

    def upsert_chunks(self, chunks: List[EvidenceChunk]) -> None:
        self._chunks = list(chunks)

    def retrieve(self, query: str, top_k: int = 6) -> List[EvidenceChunk]:
        query_terms = set(re.findall(r"[a-z0-9_]+", query.lower()))
        scored: List[Tuple[int, EvidenceChunk]] = []
        for chunk in self._chunks:
            haystack = "{0} {1}".format(chunk.text, chunk.metadata).lower()
            score = sum(1 for term in query_terms if term in haystack)
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
