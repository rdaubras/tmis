from tmis.collaboration.evaluation.metrics import OperationTiming, WorkspaceActivityMetrics


class CollaborationEvaluator:
    """Collects `OperationTiming` and `WorkspaceActivityMetrics` for
    observability (see docs/33-legal-collaboration.md — Observabilité),
    mirroring the evaluator pattern used by every other TMIS engine
    (e.g. `tmis.legal_drafting.evaluation.DraftEvaluator`)."""

    def __init__(self) -> None:
        self._timings: list[OperationTiming] = []
        self._snapshots: list[WorkspaceActivityMetrics] = []

    def record_operation_timing(self, timing: OperationTiming) -> None:
        self._timings.append(timing)

    def record_workspace_snapshot(self, snapshot: WorkspaceActivityMetrics) -> None:
        self._snapshots.append(snapshot)

    @property
    def timings(self) -> list[OperationTiming]:
        return list(self._timings)

    @property
    def snapshots(self) -> list[WorkspaceActivityMetrics]:
        return list(self._snapshots)

    def average_duration_ms(self, operation: str) -> float:
        matching = [t.duration_ms for t in self._timings if t.operation == operation]
        if not matching:
            return 0.0
        return sum(matching) / len(matching)
