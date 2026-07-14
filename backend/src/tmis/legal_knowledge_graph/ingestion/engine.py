from tmis.cabinet_knowledge.approval.engine import ApprovalEngine
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType
from tmis.cabinet_knowledge.lineage.engine import LineageEngine
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.document_intelligence.entities.ports import EntityExtractorPort
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.ingestion.schemas import IngestionResult, IngestionSourceType
from tmis.legal_knowledge_graph.semantic_engine.engine import SemanticEngine

_SOURCE_TO_KNOWLEDGE_TYPE: dict[IngestionSourceType, KnowledgeType] = {
    IngestionSourceType.INTERNAL_DOCUMENT: KnowledgeType.NOTE,
    IngestionSourceType.TEMPLATE: KnowledgeType.TEMPLATE,
    IngestionSourceType.CONTRACT: KnowledgeType.CONTRACT,
    IngestionSourceType.ANALYSIS: KnowledgeType.BEST_PRACTICE,
    IngestionSourceType.NOTE: KnowledgeType.NOTE,
    IngestionSourceType.IMPORTED_JURISPRUDENCE: KnowledgeType.JURISPRUDENCE_NOTE,
}

_SOURCE_TO_NODE_TYPE: dict[IngestionSourceType, GraphNodeType] = {
    IngestionSourceType.INTERNAL_DOCUMENT: GraphNodeType.DOCUMENT,
    IngestionSourceType.TEMPLATE: GraphNodeType.DOCUMENT,
    IngestionSourceType.CONTRACT: GraphNodeType.CONTRACT,
    IngestionSourceType.ANALYSIS: GraphNodeType.DOCUMENT,
    IngestionSourceType.NOTE: GraphNodeType.DOCUMENT,
    IngestionSourceType.IMPORTED_JURISPRUDENCE: GraphNodeType.JURISPRUDENCE,
}


class KnowledgeIngestionPipeline:
    """Import → Extraction → Classification → Enrichment → Validation
    → Publication (Sprint 25 Phase 5) — every step delegates to a
    Sprint 3/12 engine that already exists; this class only sequences
    them and links the results into the graph. Publication itself is
    a separate, explicit call (`publish`) exactly like `cabinet_
    knowledge.approval.ApprovalEngine` already requires — ingestion
    never auto-publishes."""

    def __init__(
        self,
        knowledge_space: KnowledgeSpace,
        lineage: LineageEngine,
        validation: ValidationEngine,
        approval: ApprovalEngine,
        entity_extractor: EntityExtractorPort,
        semantic_engine: SemanticEngine,
        graph: GraphEngine,
    ) -> None:
        self._knowledge_space = knowledge_space
        self._lineage = lineage
        self._validation = validation
        self._approval = approval
        self._entity_extractor = entity_extractor
        self._semantic_engine = semantic_engine
        self._graph = graph

    async def ingest(
        self,
        firm_id: str,
        source_type: IngestionSourceType,
        title: str,
        content_text: str,
        author: str,
        *,
        source_refs: tuple[str, ...] = (),
    ) -> IngestionResult:
        # Import
        knowledge_object = self._knowledge_space.create(
            firm_id,
            _SOURCE_TO_KNOWLEDGE_TYPE[source_type],
            title,
            {"text": content_text},
            author,
        )
        self._lineage.record_origin(firm_id, knowledge_object.id, source_refs, author)

        # Extraction
        entities = self._entity_extractor.extract(content_text)

        # Classification
        classification = self._semantic_engine.classify(content_text)

        # Enrichment: index for semantic search, create the graph
        # node, link every extracted entity as a related concept.
        node = self._graph.add_node(
            firm_id, _SOURCE_TO_NODE_TYPE[source_type], knowledge_object.id, title
        )
        await self._semantic_engine.index_node(firm_id, node.id, content_text)
        for entity in entities:
            entity_ref_id = f"{knowledge_object.id}::{entity.value}"
            entity_node = self._graph.add_node(
                firm_id, GraphNodeType.CONCEPT, entity_ref_id, entity.value
            )
            self._graph.link(firm_id, node.id, entity_node.id, RelationType.MENTIONS)

        # Validation (never auto-approved — human-in-the-loop, Sprint 12)
        validation_request = self._validation.submit_for_validation(
            firm_id, knowledge_object.id, author
        )

        return IngestionResult(
            knowledge_object_id=knowledge_object.id,
            graph_node_id=node.id,
            extracted_entity_labels=tuple(e.value for e in entities),
            classification_category=classification.category.value,
            classification_confidence=classification.confidence,
            validation_request_id=validation_request.id,
        )

    def publish(self, firm_id: str, knowledge_object_id: str, approver: str) -> KnowledgeObject:
        """Publication dans le Knowledge Graph — the pipeline's last
        step, always a distinct human decision (Sprint 12's
        `ApprovalEngine`) taken only after `ValidationEngine.decide`
        has already moved the object to `VALIDATED`."""
        return self._approval.publish(firm_id, knowledge_object_id, approver)
