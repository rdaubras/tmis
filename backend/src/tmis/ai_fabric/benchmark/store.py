from tmis.ai_fabric.benchmark.schemas import BenchmarkRun


class InMemoryBenchmarkStore:
    def __init__(self) -> None:
        self._runs: dict[str, list[BenchmarkRun]] = {}

    def record(self, run: BenchmarkRun) -> None:
        self._runs.setdefault(run.model_name, []).append(run)

    def history(self, model_name: str) -> list[BenchmarkRun]:
        return list(self._runs.get(model_name, []))

    def all_latest(self) -> list[BenchmarkRun]:
        return [runs[-1] for runs in self._runs.values() if runs]
