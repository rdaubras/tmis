from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SemanticMatch:
    node_id: str
    score: float
