"""Discovery Agent for the ProductPilot workflow.

This module re-exports the standalone root-level implementation so the same
agent can be used both as a package import and as an easy-to-open script.
"""

from __future__ import annotations

from ProductPilot_Discovery_Agent import (
    DiscoveryAgent,
    DiscoveryAgentConfig,
    DiscoveryAgentError,
)

__all__ = ["DiscoveryAgent", "DiscoveryAgentConfig", "DiscoveryAgentError"]

