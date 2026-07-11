from tmis.cabinet_knowledge.best_practices.engine import BestPracticeEngine
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.lessons_learned.engine import LessonLearnedEngine
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain

FIRM = "firm-a"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def test_best_practice_create_and_filter_by_domain() -> None:
    engine = BestPracticeEngine(_space())
    engine.create(
        FIRM, "Relance amiable avant contentieux", "...", LegalDomain.CIVIL, "interne", "a"
    )
    engine.create(FIRM, "Clause de médiation", "...", LegalDomain.COMMERCIAL, "interne", "a")

    civil_only = engine.list(FIRM, domain=LegalDomain.CIVIL)

    assert [p.title for p in civil_only] == ["Relance amiable avant contentieux"]


def test_lesson_learned_create_and_search_by_keyword() -> None:
    engine = LessonLearnedEngine(_space())
    engine.create(
        FIRM,
        "Delai de prescription manqué",
        context="dossier X",
        outcome="forclusion",
        recommendation="vérifier systématiquement les délais dès l'ouverture",
        author="a",
        related_case_reference="case-42",
    )
    engine.create(
        FIRM,
        "Piece manquante",
        context="dossier Y",
        outcome="rejet",
        recommendation="...",
        author="a",
    )

    matches = engine.list(FIRM, keyword="prescription")

    assert len(matches) == 1
    assert matches[0].related_case_reference == "case-42"
