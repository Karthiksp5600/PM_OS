"""Base class for all LLM providers in ProductPilot.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base class that all LLM provider integrations must implement."""

    def __init__(self, model_name: str, temperature: float = 0.2, **kwargs: Any) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.settings = kwargs

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from the model based on a prompt.

        Args:
            prompt: Rendered string prompt to send to the LLM.
            **kwargs: Provider-specific overrides (like temperature, max_tokens).

        Returns:
            The raw text response from the LLM.
        """
        pass
