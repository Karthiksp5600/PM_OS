"""Mock LLM Provider for local testing and offline execution.
"""

from __future__ import annotations

from typing import Any

from .base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Simulates LLM provider calls by returning canned or generated test JSON response."""

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Simulate generation by returning a placeholder JSON response.

        In a full implementation, we could inspect the prompt name or keywords
        to return matching simulated responses.
        """
        # Default placeholder that parses as a valid dictionary
        return '{"status": "mocked", "message": "Mocked LLM generation successful."}'
