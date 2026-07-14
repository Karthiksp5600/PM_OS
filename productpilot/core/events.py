"""Event broker system for ProductPilot agent workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass(frozen=True)
class Event:
    """Represents a single system or agent lifecycle event."""

    name: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = field(default_factory=dict)


class EventBroker:
    """Pub/sub event distributor for agent activities."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], Any]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Event], Any]) -> None:
        """Register a subscriber callback for a specific event name."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def publish(self, event: Event) -> None:
        """Distribute an event to all subscribed callbacks."""
        # Exact match subscribers
        for callback in self._subscribers.get(event.name, []):
            try:
                callback(event)
            except Exception:
                # Observers must never crash the main workflow execution
                pass

        # Wildcard subscribers (subscribing to all events with '*')
        for callback in self._subscribers.get("*", []):
            try:
                callback(event)
            except Exception:
                pass


# Global singleton event broker
event_broker = EventBroker()
