from tmis.ai_governance.audit.schemas import AIAuditEntry
from tmis.ai_governance.compliance.schemas import ComplianceVerdict
from tmis.ai_governance.explainability.schemas import ExplainabilityReport
from tmis.ai_governance.human_validation.schemas import ValidationRequest
from tmis.ai_governance.quality.schemas import GovernanceQualityBreakdown
from tmis.ai_governance.reporting.ports import ReportBuilder
from tmis.ai_governance.reporting.schemas import (
    GovernanceReport,
    ReportSection,
    ReportType,
    new_report_id,
)


class ReportGenerator:
    """The sprint's "REPORTING": one report type per governance
    concern, each rendered as human-readable sections rather than a
    raw data dump. Extensible: `register()` adds a new report type
    without modifying this class."""

    def __init__(self) -> None:
        self._builders: dict[ReportType, ReportBuilder] = {
            ReportType.EXPLAINABILITY: self._build_explainability,
            ReportType.COMPLIANCE: self._build_compliance,
            ReportType.AI_AUDIT: self._build_ai_audit,
            ReportType.VALIDATIONS: self._build_validations,
            ReportType.QUALITY: self._build_quality,
        }

    def register(self, report_type: ReportType, builder: ReportBuilder) -> None:
        self._builders[report_type] = builder

    def generate(
        self, report_type: ReportType, firm_id: str, production_id: str | None, **context: object
    ) -> GovernanceReport:
        builder = self._builders.get(report_type)
        if builder is None:
            raise ValueError(f"No report builder registered for {report_type!r}")
        return builder(firm_id, production_id, **context)

    def _build_explainability(
        self, firm_id: str, production_id: str | None, *, report: ExplainabilityReport
    ) -> GovernanceReport:
        sections = (
            ReportSection("Résumé", report.summary),
            ReportSection("Étapes suivies", "\n".join(report.steps_followed) or "Aucune"),
            ReportSection("Agents impliqués", ", ".join(report.agents_involved) or "Aucun"),
            ReportSection("Modèles utilisés", ", ".join(report.models_used) or "Aucun"),
            ReportSection(
                "Références juridiques", "\n".join(report.legal_references) or "Aucune"
            ),
            ReportSection(
                "Documents consultés", "\n".join(report.documents_consulted) or "Aucun"
            ),
            ReportSection(
                "Éléments ignorés",
                "\n".join(f"{e.description} — {e.justification}" for e in report.ignored_elements)
                or "Aucun",
            ),
        )
        return GovernanceReport(
            id=new_report_id(),
            type=ReportType.EXPLAINABILITY,
            firm_id=firm_id,
            production_id=production_id,
            title="Rapport d'explicabilité",
            sections=sections,
        )

    def _build_compliance(
        self, firm_id: str, production_id: str | None, *, verdict: ComplianceVerdict
    ) -> GovernanceReport:
        sections = (
            ReportSection(
                "Conformité", "Conforme" if verdict.compliant else "Non conforme — action requise"
            ),
            ReportSection(
                "Motifs bloquants", "\n".join(verdict.blocking_reasons) or "Aucun"
            ),
            ReportSection("Avertissements", "\n".join(verdict.warnings) or "Aucun"),
        )
        return GovernanceReport(
            id=new_report_id(),
            type=ReportType.COMPLIANCE,
            firm_id=firm_id,
            production_id=production_id,
            title="Rapport de conformité",
            sections=sections,
        )

    def _build_ai_audit(
        self, firm_id: str, production_id: str | None, *, entries: list[AIAuditEntry]
    ) -> GovernanceReport:
        lines = [
            f"{e.recorded_at.isoformat()} — {e.actor_id} — {e.action}"
            + (f" (modèle {e.model_name})" if e.model_name else "")
            for e in entries
        ]
        sections = (
            ReportSection(f"{len(entries)} entrée(s) d'audit", "\n".join(lines) or "Aucune"),
        )
        return GovernanceReport(
            id=new_report_id(),
            type=ReportType.AI_AUDIT,
            firm_id=firm_id,
            production_id=production_id,
            title="Rapport d'audit IA",
            sections=sections,
        )

    def _build_validations(
        self, firm_id: str, production_id: str | None, *, requests: list[ValidationRequest]
    ) -> GovernanceReport:
        lines = [f"{r.id} — mode {r.mode.value} — statut {r.status.value}" for r in requests]
        sections = (
            ReportSection(
                f"{len(requests)} demande(s) de validation", "\n".join(lines) or "Aucune"
            ),
        )
        return GovernanceReport(
            id=new_report_id(),
            type=ReportType.VALIDATIONS,
            firm_id=firm_id,
            production_id=production_id,
            title="Rapport des validations",
            sections=sections,
        )

    def _build_quality(
        self, firm_id: str, production_id: str | None, *, breakdown: GovernanceQualityBreakdown
    ) -> GovernanceReport:
        sections = (
            ReportSection("Score global", f"{breakdown.overall:.2f}"),
            ReportSection("Explicabilité", f"{breakdown.explainability_completeness:.2f}"),
            ReportSection("Provenance", f"{breakdown.provenance_completeness:.2f}"),
            ReportSection("Confiance", f"{breakdown.confidence_value:.2f}"),
            ReportSection("Absence de risque", f"{breakdown.risk_absence:.2f}"),
            ReportSection(
                "Couverture de validation humaine",
                f"{breakdown.human_validation_coverage:.2f}",
            ),
        )
        return GovernanceReport(
            id=new_report_id(),
            type=ReportType.QUALITY,
            firm_id=firm_id,
            production_id=production_id,
            title="Rapport de qualité",
            sections=sections,
        )
