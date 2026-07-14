"""Custom exception classes for the ProductPilot agent framework.

Defines a clean, hierarchical classification of error types.
"""

from __future__ import annotations


class ProductPilotError(Exception):
    """Base exception for all ProductPilot errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(ProductPilotError):
    """Raised when request or payload validation fails."""


class WorkflowExecutionError(ProductPilotError):
    """Raised when workflow or pipeline execution fails."""


class StageExecutionError(ProductPilotError):
    """Raised when a specific pipeline stage execution fails."""


class ConfigurationError(ProductPilotError):
    """Raised when there is an issue with the system configuration."""


class LLMError(ProductPilotError):
    """Raised when an LLM API call fails or times out."""


class RetrievalError(ProductPilotError):
    """Raised when search or retrieval providers fail."""


class EvaluationError(ProductPilotError):
    """Raised when evaluation fails to execute or schema check fails."""
