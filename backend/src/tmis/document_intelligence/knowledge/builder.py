from tmis.ai.rag.ports import Chunk
from tmis.document_intelligence.knowledge.ports import KnowledgeGraphPort
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity
from tmis.document_intelligence.schemas.knowledge import KnowledgeEdge, KnowledgeNode, NodeType
from tmis.document_intelligence.schemas.layout import BlockType, LayoutBlock
from tmis.document_intelligence.schemas.timeline import TimelineEvent

_ENTITY_NODE_TYPES: dict[EntityType, NodeType] = {
    EntityType.DATE: NodeType.DATE,
    EntityType.LAW_ARTICLE: NodeType.REFERENCE,
    EntityType.DECISION_REFERENCE: NodeType.REFERENCE,
    EntityType.REFERENCE: NodeType.REFERENCE,
}


class KnowledgeGraphBuilder:
    """Populates a `KnowledgeGraphPort` with the Document/Section/Entity/
    Date/Event/Reference/Chunk nodes described in
    docs/18-guide-knowledge-graph.md, from the artifacts already produced
    by the rest of the pipeline (layout, entities, timeline, chunks).
    """

    def update(
        self,
        graph: KnowledgeGraphPort,
        *,
        document_id: str,
        filename: str,
        layout_blocks: list[LayoutBlock],
        entities: list[ExtractedEntity],
        timeline_events: list[TimelineEvent],
        chunks: list[Chunk],
    ) -> None:
        document_node = KnowledgeNode(id=document_id, type=NodeType.DOCUMENT, label=filename)
        graph.add_node(document_node)

        for index, block in enumerate(layout_blocks):
            if block.type not in (BlockType.TITLE, BlockType.SUBTITLE):
                continue
            section_id = f"{document_id}::section::{index}"
            graph.add_node(
                KnowledgeNode(id=section_id, type=NodeType.SECTION, label=block.content)
            )
            graph.add_edge(
                KnowledgeEdge(source_id=document_id, target_id=section_id, relation="contains")
            )

        for index, entity in enumerate(entities):
            entity_id = f"{document_id}::entity::{index}"
            node_type = _ENTITY_NODE_TYPES.get(entity.type, NodeType.ENTITY)
            graph.add_node(
                KnowledgeNode(
                    id=entity_id,
                    type=node_type,
                    label=entity.value,
                    properties={"entity_type": entity.type.value},
                )
            )
            graph.add_edge(
                KnowledgeEdge(source_id=document_id, target_id=entity_id, relation="mentions")
            )

        for index, event in enumerate(timeline_events):
            event_id = f"{document_id}::event::{index}"
            graph.add_node(
                KnowledgeNode(
                    id=event_id,
                    type=NodeType.EVENT,
                    label=event.description,
                    properties={"date": event.date},
                )
            )
            graph.add_edge(
                KnowledgeEdge(source_id=document_id, target_id=event_id, relation="has_event")
            )

        for chunk in chunks:
            graph.add_node(
                KnowledgeNode(id=chunk.id, type=NodeType.CHUNK, label=chunk.content[:80])
            )
            graph.add_edge(
                KnowledgeEdge(source_id=document_id, target_id=chunk.id, relation="contains")
            )
