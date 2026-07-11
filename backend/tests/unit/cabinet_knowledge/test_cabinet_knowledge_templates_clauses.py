from tmis.cabinet_knowledge.clauses.engine import ClauseEngine
from tmis.cabinet_knowledge.clauses.schemas import ClauseVariant
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain
from tmis.cabinet_knowledge.templates.engine import CabinetTemplateEngine
from tmis.legal_drafting.templates.schemas import DocumentType

FIRM = "firm-a"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def test_create_and_list_template() -> None:
    engine = CabinetTemplateEngine(_space())

    created = engine.create_template(
        FIRM, "Mise en demeure standard", DocumentType.MISE_EN_DEMEURE, ("header", "facts"), "a"
    )

    assert created.document_type is DocumentType.MISE_EN_DEMEURE
    fetched = engine.get_template(FIRM, created.id)
    assert fetched.structure == ("header", "facts")


def test_list_templates_filters_by_document_type() -> None:
    engine = CabinetTemplateEngine(_space())
    engine.create_template(FIRM, "A", DocumentType.COURRIER, ("header",), "a")
    engine.create_template(FIRM, "B", DocumentType.CONCLUSIONS, ("header",), "a")

    result = engine.list_templates(FIRM, document_type=DocumentType.COURRIER)
    assert [t.title for t in result] == ["A"]


def test_create_clause_with_variants() -> None:
    engine = ClauseEngine(_space())
    variants = (ClauseVariant(id="v1", text="Clause de non-concurrence standard"),)

    clause = engine.create_clause(
        FIRM, "Non-concurrence", LegalDomain.COMMERCIAL, "non_concurrence", variants, "a"
    )

    assert len(clause.variants) == 1


def test_add_variant_bumps_version_via_update_content() -> None:
    engine = ClauseEngine(_space())
    variants = (ClauseVariant(id="v1", text="Version courte"),)
    clause = engine.create_clause(
        FIRM, "Non-concurrence", LegalDomain.COMMERCIAL, "non_concurrence", variants, "a"
    )

    updated = engine.add_variant(
        FIRM, clause.id, ClauseVariant(id="v2", text="Version longue"), actor="a"
    )

    assert len(updated.variants) == 2


def test_search_clauses_by_domain_type_and_keyword() -> None:
    engine = ClauseEngine(_space())
    engine.create_clause(
        FIRM,
        "Non-concurrence",
        LegalDomain.COMMERCIAL,
        "non_concurrence",
        (ClauseVariant(id="v1", text="Interdiction de concurrence pendant 2 ans"),),
        "a",
    )
    engine.create_clause(
        FIRM,
        "Confidentialité",
        LegalDomain.COMMERCIAL,
        "confidentialite",
        (ClauseVariant(id="v1", text="Obligation de confidentialité"),),
        "a",
    )

    by_type = engine.search(FIRM, clause_type="confidentialite")
    assert [c.title for c in by_type] == ["Confidentialité"]

    by_keyword = engine.search(FIRM, keyword="concurrence")
    assert [c.title for c in by_keyword] == ["Non-concurrence"]

    by_domain = engine.search(FIRM, domain=LegalDomain.SOCIAL)
    assert by_domain == []
