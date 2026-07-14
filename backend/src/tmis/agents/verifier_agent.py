from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai_governance.bias_detection.engine import BiasDetectionEngine
from tmis.ai_governance.hallucination_detection.engine import HallucinationDetectionEngine
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.legal_reasoning.conflicts.engine import HeuristicConflictDetector
from tmis.legal_reasoning.conflicts.ports import ConflictDetectorPort

_CASE_STORE_CONNECTOR = "case_store"

# Keys under which Analysis (`narrative`) and Synthesis (`synthesis_note`,
# `executive_summary`) put the only free text in their `result` that is
# actually model-generated rather than a deterministic aggregation (see
# `AnalysisAgent._generate_narrative`, `SynthesisAgent._generate_synthesis_note`
# and `CaseSummaryGenerator.generate` — `chronological_summary`/
# `documentary_summary`/`case_status` never call a model). These key names
# are read as-is, never renamed, per the Sprint 31 scope.
_NARRATIVE_KEYS = ("narrative", "synthesis_note", "executive_summary")


class VerifierAgent:
    """Checks coherence, citations, contradictions and duplicates (docs/05).

    Every other agent's output is routed through this agent before the
    orchestrator fuses a final response. Sprint 1 only checked that any
    citation claimed actually carries a traceable excerpt/reference.
    Sprint 31 (see docs/159-architecture-agent-verificateur.md) adds three
    more checks, each a thin composition over an existing engine — this
    agent never re-implements conflict/hallucination/bias detection:

    - **Case coherence**: if `output.citations` carries a `Citation` whose
      `connector == "case_store"` (the convention `SynthesisAgent` already
      uses to cite the case it summarized — `AgentOutput` itself has no
      `case_id` field and Sprint 31 must not add one), the matching
      `CaseProfile` is loaded via `CaseStorePort` and its `facts`/
      `timeline_inconsistencies` are handed to
      `HeuristicConflictDetector.detect()` unchanged.
    - **Hallucinations**: every narrative string found in `output.result`
      (see `_NARRATIVE_KEYS`) is scanned by
      `HallucinationDetectionEngine.scan()`.
    - **Bias**: the same narrative strings are scanned by
      `BiasDetectionEngine.scan()`.

    Every finding becomes a warning — never a content deletion or rewrite,
    the same principle the two detection engines themselves follow — and
    confidence is degraded through one explicit, documented cascade: for
    each of the four check categories above (citation completeness,
    conflicts, hallucinations, bias) that raised at least one warning
    *during this call*, count one "signal". `HIGH` drops to `MEDIUM` once
    at least one signal fired; `MEDIUM` drops to `LOW` once at least two
    distinct signal categories fired (evaluated after the first rule, so a
    `HIGH` input with two or more signal categories reaches `LOW` in the
    same call). Confidence is never upgraded, and pre-existing warnings
    already present on `output.warnings` before this call — which may
    have nothing to do with what the Verifier itself checks — no longer
    influence this cascade; only signals this agent verifies itself do
    (a deliberate replacement of the Sprint 1 "any warning at all"
    blanket rule, which conflated upstream warnings with the Verifier's
    own assessment).
    """

    name = "verifier"

    def __init__(
        self,
        *,
        case_store: CaseStorePort | None = None,
        conflict_detector: ConflictDetectorPort | None = None,
        hallucination_engine: HallucinationDetectionEngine | None = None,
        bias_engine: BiasDetectionEngine | None = None,
    ) -> None:
        self._case_store: CaseStorePort = case_store or InMemoryCaseStore()
        self._conflict_detector: ConflictDetectorPort = (
            conflict_detector or HeuristicConflictDetector()
        )
        self._hallucination_engine = hallucination_engine or HallucinationDetectionEngine()
        self._bias_engine = bias_engine or BiasDetectionEngine()

    async def verify(self, output: AgentOutput) -> AgentOutput:
        warnings = list(output.warnings)
        signal_categories = 0

        citation_warnings = self._check_citations(output)
        if citation_warnings:
            signal_categories += 1
            warnings.extend(citation_warnings)

        conflict_warnings = self._check_case_coherence(output)
        if conflict_warnings:
            signal_categories += 1
            warnings.extend(conflict_warnings)

        narrative_texts = self._extract_narrative_texts(output.result)

        hallucination_warnings = self._check_hallucinations(narrative_texts)
        if hallucination_warnings:
            signal_categories += 1
            warnings.extend(hallucination_warnings)

        bias_warnings = self._check_bias(narrative_texts)
        if bias_warnings:
            signal_categories += 1
            warnings.extend(bias_warnings)

        confidence = self._degrade_confidence(output.confidence, signal_categories)

        return AgentOutput(
            result=output.result,
            citations=output.citations,
            confidence=confidence,
            warnings=warnings,
        )

    @staticmethod
    def _check_citations(output: AgentOutput) -> list[str]:
        return [
            f"Citation {citation.source_id!r} is missing a traceable excerpt or reference."
            for citation in output.citations
            if not citation.excerpt or not citation.reference
        ]

    def _check_case_coherence(self, output: AgentOutput) -> list[str]:
        case_id = self._resolve_case_id(output)
        if case_id is None:
            return []
        case_profile = self._case_store.get(case_id)
        if case_profile is None:
            return []
        conflicts = self._conflict_detector.detect(
            case_profile.facts, case_profile.timeline_inconsistencies
        )
        return [
            f"Conflict detected ({conflict.type.value}): {conflict.description} "
            f"{conflict.explanation}"
            for conflict in conflicts
        ]

    @staticmethod
    def _resolve_case_id(output: AgentOutput) -> str | None:
        for citation in output.citations:
            if citation.connector == _CASE_STORE_CONNECTOR:
                return citation.source_id
        return None

    @staticmethod
    def _extract_narrative_texts(result: dict[str, object]) -> list[str]:
        texts: list[str] = []
        for key in _NARRATIVE_KEYS:
            value = result.get(key)
            if isinstance(value, str) and value:
                texts.append(value)

        nested = result.get("synthesis")
        if isinstance(nested, dict):
            for key in _NARRATIVE_KEYS:
                value = nested.get(key)
                if isinstance(value, str) and value:
                    texts.append(value)

        return texts

    def _check_hallucinations(self, texts: list[str]) -> list[str]:
        return [
            f"Hallucination risk: {alert.reason} ({alert.recommendation})"
            for text in texts
            for alert in self._hallucination_engine.scan(text)
        ]

    def _check_bias(self, texts: list[str]) -> list[str]:
        return [
            f"Bias detected ({finding.category}): {finding.description} — {finding.explanation}"
            for text in texts
            for finding in self._bias_engine.scan(text)
        ]

    @staticmethod
    def _degrade_confidence(
        confidence: ConfidenceLevel, signal_categories: int
    ) -> ConfidenceLevel:
        if signal_categories >= 1 and confidence == ConfidenceLevel.HIGH:
            confidence = ConfidenceLevel.MEDIUM
        if signal_categories >= 2 and confidence == ConfidenceLevel.MEDIUM:
            confidence = ConfidenceLevel.LOW
        return confidence

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "VerifierAgent is invoked via `verify(output)` on another agent's output, "
            "not directly as a graph entry point."
        )
