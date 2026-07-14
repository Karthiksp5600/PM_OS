"""Base evaluation interfaces for ProductPilot agents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from .models import EvaluationResult


class BaseEvaluator(ABC):
    """Abstract base class that all quality evaluation check suites must implement."""

    @abstractmethod
    def evaluate(self, context: Any) -> EvaluationResult:
        """Run validation rules on the given context/artifacts."""
        pass


class CompositeEvaluator(BaseEvaluator):
    """Groups multiple evaluators together to return a sequence of checks."""

    def __init__(self, evaluators: list[BaseEvaluator]) -> None:
        self.evaluators = evaluators

    def evaluate(self, context: Any) -> list[EvaluationResult]:
        """Execute all child evaluators and return their combined results."""
        return [evaluator.evaluate(context) for evaluator in self.evaluators]
