"""Generic metrics collection framework for ProductPilot agents.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any, Sequence

from .models import RuntimeMetrics
from .utils import estimate_tokens, utc_timestamp


class MetricsCollector:
    """Manages telemetry collection (latency, token usage, costs) for agent runs."""

    def __init__(self) -> None:
        self._start = perf_counter()

    def _latency(self) -> float:
        return round((perf_counter() - self._start) * 1000, 3)

    def _estimate_cost(self, prompt: str, response: str) -> float:
        # Standard pricing estimate (e.g. $2.00 per million tokens)
        tokens = estimate_tokens(prompt) + estimate_tokens(response)
        return round(tokens * 0.000002, 6)

    def collect_runtime(
        self,
        prompt: str = "",
        response: str = "",
        retries: int = 0,
        retrieval_count: int = 0,
        citation_count: int = 0,
    ) -> RuntimeMetrics:
        """Create and populate a standard RuntimeMetrics instance."""
        latency = self._latency()
        cost = self._estimate_cost(prompt, response)

        return RuntimeMetrics(
            latency_ms=latency,
            token_input=estimate_tokens(prompt),
            token_output=estimate_tokens(response),
            cost_usd=cost,
            estimated_cost_usd=cost,
            retries=retries,
            retry_count=retries,
            retrieval_count=retrieval_count,
            citation_count=citation_count,
            timestamp=utc_timestamp(),
        )

    @staticmethod
    def calculate_average(values: Sequence[float]) -> float:
        """Helper to calculate average values safely."""
        if not values:
            return 0.0
        return round(sum(values) / len(values), 3)
