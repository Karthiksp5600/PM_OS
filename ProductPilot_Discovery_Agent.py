"""Compatibility wrapper for the ProductPilot discovery agent."""

from __future__ import annotations

from productpilot.agents.discovery_agent import (
    DiscoveryAgent,
    DiscoveryAgentConfig,
    DiscoveryAgentError,
    example_request,
    process_request,
)

__all__ = ["DiscoveryAgent", "DiscoveryAgentConfig", "DiscoveryAgentError", "example_request", "process_request"]
