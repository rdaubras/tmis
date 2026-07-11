from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class FusionSource:
    model_name: str
    text: str
    citation_count: int


@dataclass(frozen=True, slots=True)
class FusedResponse:
    fused_text: str
    sources: tuple[FusionSource, ...] = field(default_factory=tuple)
    provenance: dict[str, str] = field(default_factory=dict)
