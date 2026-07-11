from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QualityBreakdown:
    knowledge_object_id: str
    freshness: float
    completeness: float
    usage: float
    human_validation: float
    coherence: float

    @property
    def overall(self) -> float:
        return (
            self.freshness
            + self.completeness
            + self.usage
            + self.human_validation
            + self.coherence
        ) / 5
