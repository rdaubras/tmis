from typing import Protocol

from tmis.ai_fabric.benchmark.schemas import BenchmarkRun


class BenchmarkStorePort(Protocol):
    def record(self, run: BenchmarkRun) -> None: ...

    def history(self, model_name: str) -> list[BenchmarkRun]: ...

    def all_latest(self) -> list[BenchmarkRun]: ...
