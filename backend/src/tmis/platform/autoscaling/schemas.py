from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AutoscalingPolicy:
    min_replicas: int
    max_replicas: int
    target_cpu_percent: int
    target_memory_percent: int

    def __post_init__(self) -> None:
        if self.min_replicas > self.max_replicas:
            raise ValueError("min_replicas cannot exceed max_replicas")
