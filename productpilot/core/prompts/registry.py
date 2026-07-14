"""Prompt registration and version lookup system.
"""

from __future__ import annotations

from dataclasses import dataclass
from string import Template


@dataclass(frozen=True)
class Prompt:
    """Represents a versioned system + user prompt pair."""

    name: str
    version: str
    system: str
    user: Template

    def render(self, **kwargs) -> str:
        """Render the user prompt template with keyword arguments."""
        return self.user.safe_substitute(**kwargs)


class PromptRegistry:
    """Manages versioned prompts for all ProductPilot agents, supporting dynamic A/B testing."""

    def __init__(self) -> None:
        # Structure: prompt_name -> version_string -> Prompt
        self._registry: dict[str, dict[str, Prompt]] = {}
        self._default_versions: dict[str, str] = {}

    def register(self, prompt: Prompt, is_default: bool = True) -> None:
        """Register a versioned prompt. Marks it as default if specified."""
        if prompt.name not in self._registry:
            self._registry[prompt.name] = {}
        self._registry[prompt.name][prompt.version] = prompt

        if is_default or prompt.name not in self._default_versions:
            self._default_versions[prompt.name] = prompt.version

    def get(self, name: str, version: str | None = None) -> Prompt:
        """Retrieve a prompt by name. Fallback to default version if none specified."""
        if name not in self._registry:
            raise KeyError(f"Prompt '{name}' is not registered.")

        target_version = version or self._default_versions.get(name)
        if not target_version or target_version not in self._registry[name]:
            raise KeyError(f"Prompt '{name}' has no registered version '{target_version}'.")

        return self._registry[name][target_version]

    def list_prompts(self) -> dict[str, list[str]]:
        """Return a mapping of all registered prompt names to their available versions."""
        return {name: list(versions.keys()) for name, versions in self._registry.items()}


# Global Registry Instance
prompt_registry = PromptRegistry()
