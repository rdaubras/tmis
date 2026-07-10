from tmis.case_intelligence.evidence.schemas import EvidenceConfidence, EvidenceLink
from tmis.case_intelligence.facts.schemas import Fact

_HIGH_CONFIDENCE_THRESHOLD = 0.8
_LOW_CONFIDENCE_THRESHOLD = 0.5


class EvidenceLinker:
    """Implements `EvidenceLinkerPort`: derives an `EvidenceLink` per
    document backing a fact, weighting the confidence level by how the
    document relates to the fact (its origin vs. a later corroboration)
    and by the fact's own confidence score (see
    docs/19-case-intelligence.md).
    """

    def link(self, fact: Fact) -> list[EvidenceLink]:
        links = [
            EvidenceLink(
                fact_id=fact.id,
                document_id=document_id,
                confidence=self._origin_confidence(fact),
            )
            for document_id in fact.source_document_ids
        ]
        links += [
            EvidenceLink(
                fact_id=fact.id,
                document_id=document_id,
                confidence=self._corroboration_confidence(fact),
            )
            for document_id in fact.confirming_document_ids
        ]
        return links

    def _origin_confidence(self, fact: Fact) -> EvidenceConfidence:
        if fact.confidence < _LOW_CONFIDENCE_THRESHOLD:
            return EvidenceConfidence.WEAK
        if fact.confidence >= _HIGH_CONFIDENCE_THRESHOLD:
            return EvidenceConfidence.DIRECT
        return EvidenceConfidence.CIRCUMSTANTIAL

    def _corroboration_confidence(self, fact: Fact) -> EvidenceConfidence:
        if fact.confidence < _LOW_CONFIDENCE_THRESHOLD:
            return EvidenceConfidence.WEAK
        return EvidenceConfidence.CORROBORATING
