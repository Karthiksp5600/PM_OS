"""Dependency Injection container for the ProductPilot agent framework.

Manages registrations of LLMs, Retrievers, Prompt Registries, and logger instances.
"""

from __future__ import annotations

from typing import Any


class DependencyContainer:
    """A thread-safe registry container for service dependency injection."""

    def __init__(self) -> None:
        self._registry: dict[str, Any] = {}

    def register(self, key: str, dependency: Any) -> None:
        """Register a dependency with a specific string key."""
        self._registry[key] = dependency

    def get(self, key: str) -> Any:
        """Retrieve a registered dependency. Raises ValueError if not found."""
        if key not in self._registry:
            raise ValueError(f"Dependency '{key}' has not been registered in the container.")
        return self._registry[key]

    def has(self, key: str) -> bool:
        """Check if a dependency is registered."""
        return key in self._registry

    def clear(self) -> None:
        """Clear all registered dependencies."""
        self._registry.clear()


# Global Singleton Container instance for easy imports if needed
container = DependencyContainer()
