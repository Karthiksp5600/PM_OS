"""Connector base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from productpilot.discovery.schemas import NormalizedRecord


class SourceConnector(ABC):
    source_name: str

    @abstractmethod
    def fetch(self) -> list[NormalizedRecord]:
        raise NotImplementedError
