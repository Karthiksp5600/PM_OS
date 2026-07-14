"""
ProductPilot Discovery Agent

Public API for the Discovery package.

Only stable interfaces should be exported here.
Everything else is considered internal implementation.
"""

from .agent import (
    BaseAgent,
    DiscoveryAgent,
    DiscoveryResponse,
    run_discovery,
)

from .schemas import (
    DiscoveryRequest,
    DiscoveryArtifact,
    DiscoveryResponse as DiscoverySchemaResponse,
)

from .config import (
    DiscoveryConfig,
    settings,
)

from .types import (
    WorkflowMode,
    DiscoveryIntent,
    EvaluationStatus,
    SourceType,
    JourneyStage,
)

__version__ = "0.1.0"

__all__ = [

    # Main API

    "DiscoveryAgent",

    "run_discovery",

    "DiscoveryRequest",

    "DiscoveryResponse",

    "DiscoverySchemaResponse",

    # Base

    "BaseAgent",

    # Config

    "DiscoveryConfig",

    "settings",

    # Enums

    "WorkflowMode",

    "DiscoveryIntent",

    "EvaluationStatus",

    "SourceType",

    "JourneyStage",
]