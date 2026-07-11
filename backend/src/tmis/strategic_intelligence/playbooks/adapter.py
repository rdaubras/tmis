from tmis.cabinet_knowledge.playbooks.engine import PlaybookEngine
from tmis.cabinet_knowledge.playbooks.schemas import Playbook


class PlaybookAdapter:
    """Thin adapter reusing `cabinet_knowledge.playbooks.PlaybookEngine`
    directly — per the sprint's explicit instruction to reuse the
    Cabinet Knowledge Engine's playbooks rather than reimplement
    them. No new storage; every playbook returned is already validated
    (`PlaybookEngine.list_playbooks` only ever returns published,
    knowledge-space-backed playbooks)."""

    def __init__(self, playbook_engine: PlaybookEngine) -> None:
        self._playbook_engine = playbook_engine

    def find_playbooks_for_case_type(self, firm_id: str, case_type: str) -> list[Playbook]:
        return self._playbook_engine.list_playbooks(firm_id, case_type=case_type)

    def steps_as_recommended_actions(self, playbook: Playbook) -> tuple[str, ...]:
        return tuple(step.title for step in playbook.steps)
