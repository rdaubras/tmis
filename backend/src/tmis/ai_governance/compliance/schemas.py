from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ComplianceVerdict:
    """The final answer to "peut-on considérer cette production comme
    définitive ?" — always split into blocking reasons (policy
    failures and high/critical risks) versus non-blocking warnings
    (lower-severity risks), never a bare boolean."""

    production_id: str
    compliant: bool
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
