from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CaseSummary:
    executive_summary: str
    chronological_summary: str
    documentary_summary: str
    case_status: str
    open_points: tuple[str, ...] = ()
