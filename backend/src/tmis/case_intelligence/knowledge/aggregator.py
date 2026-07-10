from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.relationships.ports import CaseGraphPort
from tmis.case_intelligence.relationships.schemas import CaseEdge, CaseNode, CaseNodeType


class CaseKnowledgeAggregator:
    """Populates a `CaseGraphPort` with the Actor/Document/Event/Fact/
    Exhibit/Issue nodes described in docs/19-case-intelligence.md, from
    the artifacts already gathered in a `CaseProfile`.

    Idempotent: nodes are keyed by a stable id derived from the source
    object's own id, so calling `update()` again after new documents are
    processed simply adds/overwrites nodes rather than duplicating them.
    """

    def update(self, graph: CaseGraphPort, profile: CaseProfile) -> None:
        for document_id in profile.document_ids:
            graph.add_node(
                CaseNode(
                    id=f"document::{document_id}",
                    type=CaseNodeType.DOCUMENT,
                    label=document_id,
                )
            )

        for actor in profile.actors:
            actor_node_id = f"actor::{actor.id}"
            graph.add_node(
                CaseNode(
                    id=actor_node_id,
                    type=CaseNodeType.ACTOR,
                    label=actor.name,
                    properties={"actor_type": actor.type.value},
                )
            )
            for document_id in actor.source_document_ids:
                graph.add_edge(
                    CaseEdge(
                        source_id=actor_node_id,
                        target_id=f"document::{document_id}",
                        relation="mentioned_in",
                    )
                )

        for index, entry in enumerate(profile.timeline):
            event_node_id = f"event::{profile.case_id}::{index}"
            graph.add_node(
                CaseNode(
                    id=event_node_id,
                    type=CaseNodeType.EVENT,
                    label=entry.description,
                    properties={"date": entry.date},
                )
            )
            for document_id in entry.document_ids:
                graph.add_edge(
                    CaseEdge(
                        source_id=event_node_id,
                        target_id=f"document::{document_id}",
                        relation="occurred_in",
                    )
                )

        for fact in profile.facts:
            graph.add_node(
                CaseNode(id=f"fact::{fact.id}", type=CaseNodeType.FACT, label=fact.description)
            )

        for link in profile.evidence_links:
            exhibit_node_id = f"exhibit::{link.document_id}"
            graph.add_node(
                CaseNode(
                    id=exhibit_node_id,
                    type=CaseNodeType.EXHIBIT,
                    label=link.document_id,
                    properties={"confidence": link.confidence.value},
                )
            )
            graph.add_edge(
                CaseEdge(
                    source_id=f"fact::{link.fact_id}",
                    target_id=exhibit_node_id,
                    relation="supported_by",
                )
            )

        for issue in profile.legal_issues:
            issue_node_id = f"issue::{issue.id}"
            graph.add_node(
                CaseNode(id=issue_node_id, type=CaseNodeType.ISSUE, label=issue.description)
            )
            for fact_id in issue.related_fact_ids:
                graph.add_edge(
                    CaseEdge(
                        source_id=issue_node_id, target_id=f"fact::{fact_id}", relation="relates_to"
                    )
                )
