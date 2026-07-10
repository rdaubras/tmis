import time
from datetime import UTC, datetime
from types import TracebackType

from tmis.collaboration.evaluation.evaluator import CollaborationEvaluator
from tmis.collaboration.evaluation.metrics import OperationTiming


class OperationTimer:
    """Context manager measuring one operation's wall-clock duration and
    recording it into a `CollaborationEvaluator` (see
    docs/33-legal-collaboration.md — Observabilité). Usage::

        with OperationTimer(evaluator, "task.create"):
            task_service.create(...)
    """

    def __init__(self, evaluator: CollaborationEvaluator, operation: str) -> None:
        self._evaluator = evaluator
        self._operation = operation
        self._start = 0.0

    def __enter__(self) -> "OperationTimer":
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        duration_ms = (time.perf_counter() - self._start) * 1000
        self._evaluator.record_operation_timing(
            OperationTiming(
                operation=self._operation,
                duration_ms=duration_ms,
                occurred_at=datetime.now(UTC),
            )
        )
