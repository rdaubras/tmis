from tmis.case_intelligence.actors.schemas import Actor, ActorType
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.evidence.schemas import EvidenceConfidence, EvidenceLink
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.issues.schemas import LegalIssue
from tmis.case_intelligence.knowledge.aggregator import CaseKnowledgeAggregator
from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.case_intelligence.relationships.schemas import CaseNodeType
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry


def _profile() -> CaseProfile:
    profile = CaseProfile(case_id="case-1", title="Dupont c. ACME")
    profile.document_ids = {"doc-1"}
    profile.actors = [
        Actor(id="a1", type=ActorType.PERSON, name="Jean Dupont", source_document_ids={"doc-1"})
    ]
    profile.timeline = [
        CaseTimelineEntry(
            date="12 janvier 2019", description="Signature", document_ids=("doc-1",), confidence=0.7
        )
    ]
    profile.facts = [
        Fact(id="f1", description="Signature", confidence=0.7, source_document_ids={"doc-1"})
    ]
    profile.evidence_links = [
        EvidenceLink(fact_id="f1", document_id="doc-1", confidence=EvidenceConfidence.DIRECT)
    ]
    profile.legal_issues = [LegalIssue(id="i1", description="Question", related_fact_ids=("f1",))]
    return profile


def test_aggregator_creates_a_node_per_document() -> None:
    graph = InMemoryCaseGraph()
    CaseKnowledgeAggregator().update(graph, _profile())
    assert graph.get_node("document::doc-1") is not None


def test_aggregator_links_actor_to_source_document() -> None:
    graph = InMemoryCaseGraph()
    CaseKnowledgeAggregator().update(graph, _profile())
    neighbors = graph.get_neighbors("actor::a1")
    assert neighbors == [graph.get_node("document::doc-1")]


def test_aggregator_links_event_to_its_document() -> None:
    graph = InMemoryCaseGraph()
    CaseKnowledgeAggregator().update(graph, _profile())
    neighbors = graph.get_neighbors("event::case-1::0")
    assert graph.get_node("document::doc-1") in neighbors


def test_aggregator_links_fact_to_exhibit() -> None:
    graph = InMemoryCaseGraph()
    CaseKnowledgeAggregator().update(graph, _profile())
    neighbors = graph.get_neighbors("fact::f1")
    assert neighbors[0].type == CaseNodeType.EXHIBIT


def test_aggregator_links_issue_to_related_fact() -> None:
    graph = InMemoryCaseGraph()
    CaseKnowledgeAggregator().update(graph, _profile())
    neighbors = graph.get_neighbors("issue::i1")
    assert neighbors == [graph.get_node("fact::f1")]


def test_aggregator_creates_node_per_actor_fact_and_issue() -> None:
    graph = InMemoryCaseGraph()
    CaseKnowledgeAggregator().update(graph, _profile())
    assert graph.node_count == 6  # document, actor, event, fact, exhibit, issue
    assert graph.edge_count == 4  # actor->doc, event->doc, fact->exhibit, issue->fact
