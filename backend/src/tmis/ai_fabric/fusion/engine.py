from tmis.ai_fabric.consensus.schemas import ModelPosition
from tmis.ai_fabric.evaluation.engine import ResponseEvaluator
from tmis.ai_fabric.fusion.schemas import FusedResponse, FusionSource


class FusionEngine:
    """The sprint's "FUSION ENGINE": assembles several models'
    responses into a single answer while preserving citations,
    provenance, and each source's own explanation — unlike
    `tmis.ai_fabric.consensus`, which *selects* one representative
    text, fusion keeps every source's contribution intact, tagged by
    origin, rather than collapsing them into one voice."""

    def __init__(self, evaluator: ResponseEvaluator | None = None) -> None:
        self._evaluator = evaluator or ResponseEvaluator()

    def fuse(self, positions: list[ModelPosition]) -> FusedResponse:
        sources: list[FusionSource] = []
        segments: list[str] = []
        provenance: dict[str, str] = {}

        for index, position in enumerate(positions):
            metrics = self._evaluator.evaluate(position.text)
            sources.append(
                FusionSource(
                    model_name=position.model_name,
                    text=position.text,
                    citation_count=metrics.citation_count,
                )
            )
            segment_id = f"segment-{index + 1}"
            segments.append(f"[{position.model_name}] {position.text}")
            provenance[segment_id] = position.model_name

        return FusedResponse(
            fused_text="\n\n".join(segments), sources=tuple(sources), provenance=provenance
        )
