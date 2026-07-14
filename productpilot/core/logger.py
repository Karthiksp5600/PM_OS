"""Structured logging and tracing for ProductPilot agents.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, is_dataclass
from time import perf_counter
from typing import Any
from uuid import uuid4


class JsonFormatter(logging.Formatter):
    """Formats LogRecord payloads into structured JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "trace_id"):
            payload["trace_id"] = record.trace_id

        if hasattr(record, "workflow_id"):
            payload["workflow_id"] = record.workflow_id

        if hasattr(record, "project_id"):
            payload["project_id"] = record.project_id

        if hasattr(record, "stage"):
            payload["stage"] = record.stage

        if hasattr(record, "metadata"):
            payload["metadata"] = record.metadata

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=False)


def create_logger(name: str = "productpilot.agent") -> logging.Logger:
    """Create or retrieve a structured JSON logger instance."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = create_logger()


class TraceContext:
    """Uniquely identifies a single execution trace for a workflow request."""

    def __init__(self, workflow_id: str, project_id: str) -> None:
        self.trace_id = uuid4().hex
        self.workflow_id = workflow_id
        self.project_id = project_id


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


def log_event(
    *,
    level: int,
    message: str,
    trace: TraceContext,
    stage: str | None = None,
    metadata: Any | None = None,
) -> None:
    """Write a structured JSON log entry."""
    logger.log(
        level,
        message,
        extra={
            "trace_id": trace.trace_id,
            "workflow_id": trace.workflow_id,
            "project_id": trace.project_id,
            "stage": stage,
            "metadata": _serialize(metadata),
        },
    )


def stage_started(stage: str, trace: TraceContext) -> None:
    log_event(level=logging.INFO, message=f"{stage} started", trace=trace, stage=stage)


def stage_completed(stage: str, trace: TraceContext, metadata: Any | None = None) -> None:
    log_event(
        level=logging.INFO,
        message=f"{stage} completed",
        trace=trace,
        stage=stage,
        metadata=metadata,
    )


def log_exception(exc: Exception, trace: TraceContext, stage: str) -> None:
    """Log an exception payload inside JSON format."""
    logger.error(
        str(exc),
        exc_info=True,
        extra={
            "trace_id": trace.trace_id,
            "workflow_id": trace.workflow_id,
            "project_id": trace.project_id,
            "stage": stage,
            "metadata": {
                "exception_type": type(exc).__name__,
            },
        },
    )


class Timer:
    """Context manager for timing pipeline stage latency."""

    def __init__(self, trace: TraceContext, stage: str) -> None:
        self.trace = trace
        self.stage = stage
        self.start = 0.0

    def __enter__(self) -> Timer:
        self.start = perf_counter()
        stage_started(self.stage, self.trace)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        duration = (perf_counter() - self.start) * 1000

        if exc:
            log_exception(exc, self.trace, self.stage)
            return False

        stage_completed(self.stage, self.trace, {"latency_ms": round(duration, 2)})
        return True


def log_prompt(prompt: str, trace: TraceContext) -> None:
    log_event(
        level=logging.DEBUG,
        message="Prompt",
        trace=trace,
        metadata={"prompt": prompt},
    )


def log_llm_response(response: str, trace: TraceContext) -> None:
    log_event(
        level=logging.DEBUG,
        message="LLM Response",
        trace=trace,
        metadata={"response": response},
    )


def log_retrieval(query: str, retrieved: int, trace: TraceContext) -> None:
    log_event(
        level=logging.INFO,
        message="Retrieval completed",
        trace=trace,
        stage="retrieval",
        metadata={"query": query, "documents": retrieved},
    )


def log_evaluation(score: float, passed: bool, trace: TraceContext) -> None:
    log_event(
        level=logging.INFO,
        message="Evaluation completed",
        trace=trace,
        stage="evaluation",
        metadata={"score": score, "passed": passed},
    )
