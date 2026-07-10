from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.issues.schemas import IssueStatus
from tmis.case_intelligence.summaries.ports import SummaryKernelPort
from tmis.case_intelligence.summaries.schemas import CaseSummary


class CaseSummaryGenerator:
    """Implements `SummaryGeneratorPort`.

    Three of the four summaries are deterministic aggregations (no model
    call needed); the executive summary is the one piece that benefits
    from a model's synthesis, so it is the only one produced through
    `TMISKernel.complete()` (see docs/19-case-intelligence.md and the
    Sprint 4 constraint that no business logic calls an LLM directly).
    """

    def __init__(self, kernel: SummaryKernelPort) -> None:
        self._kernel = kernel

    async def generate(self, profile: CaseProfile) -> CaseSummary:
        chronological_summary = self._chronological_summary(profile)
        documentary_summary = self._documentary_summary(profile)
        case_status = self._case_status(profile)
        open_points = self._open_points(profile)

        prompt = (
            f"Rédige une synthèse exécutive du dossier « {profile.title} ».\n"
            f"Statut : {case_status}\n"
            f"Chronologie : {chronological_summary}\n"
            f"Points à éclaircir : {'; '.join(open_points) or 'aucun'}"
        )
        response = await self._kernel.complete(prompt)

        return CaseSummary(
            executive_summary=response.text,
            chronological_summary=chronological_summary,
            documentary_summary=documentary_summary,
            case_status=case_status,
            open_points=tuple(open_points),
        )

    def _chronological_summary(self, profile: CaseProfile) -> str:
        if not profile.timeline:
            return "Aucun événement daté n'a encore été identifié."
        return " ; ".join(f"{entry.date} : {entry.description}" for entry in profile.timeline)

    def _documentary_summary(self, profile: CaseProfile) -> str:
        return (
            f"{len(profile.document_ids)} document(s) analysé(s), "
            f"{len(profile.facts)} fait(s) et {len(profile.actors)} acteur(s) identifiés."
        )

    def _case_status(self, profile: CaseProfile) -> str:
        if profile.is_deleted:
            return "Dossier clôturé"
        open_issues = [i for i in profile.legal_issues if i.status == IssueStatus.OPEN]
        if open_issues:
            return f"En cours — {len(open_issues)} question(s) juridique(s) ouverte(s)"
        return "En cours"

    def _open_points(self, profile: CaseProfile) -> list[str]:
        points = [
            issue.description
            for issue in profile.legal_issues
            if issue.status == IssueStatus.OPEN
        ]
        points += [
            f"Incohérence temporelle au {inconsistency.date}"
            for inconsistency in profile.timeline_inconsistencies
        ]
        return points
