"""
Base Agent Framework.

Every ProductPilot agent inherits from this class.

Responsibilities
----------------
- Request validation
- Workflow execution
- AI evaluation
- Metrics
- Logging
- Lifecycle hooks
- Error handling

Business logic belongs only in execute().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .logger import TraceContext, log_exception
from .metrics import MetricsCollector

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


class BaseAgent(ABC, Generic[RequestT, ResponseT]):

    def __init__(
        self,
        *,
        name: str,
        workflow,
        evaluator=None,
        metrics: MetricsCollector | None = None,
    ) -> None:

        self._name = name

        self.workflow = workflow

        self.evaluator = evaluator

        self.metrics = metrics or MetricsCollector()

    @property
    def name(self) -> str:
        return self._name

    async def run(
        self,
        request: RequestT,
    ) -> ResponseT:

        trace = self._build_trace(request)

        try:

            await self.validate(request)

            await self.before_execute(request)

            response = await self.execute(request)

            await self.after_execute(request, response)

            if self.evaluator:

                await self.evaluate(request, response)

            await self.finalize(request, response)

            return response

        except Exception as exc:

            log_exception(
                exc,
                trace,
                self.name,
            )

            raise

    @abstractmethod
    async def execute(
        self,
        request: RequestT,
    ) -> ResponseT:
        ...

    async def validate(
        self,
        request: RequestT,
    ):
        pass

    async def before_execute(
        self,
        request: RequestT,
    ):
        pass

    async def after_execute(
        self,
        request: RequestT,
        response: ResponseT,
    ):
        pass

    async def evaluate(
        self,
        request: RequestT,
        response: ResponseT,
    ):
        if self.evaluator:

            self.evaluator.evaluate(response)

    async def finalize(
        self,
        request: RequestT,
        response: ResponseT,
    ):
        pass

    def _build_trace(
        self,
        request,
    ) -> TraceContext:

        return TraceContext(

            workflow_id=request.workflow_id,

            project_id=request.project_id,

        )