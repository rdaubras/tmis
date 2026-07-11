from tmis.ai_team.capabilities.catalog import domain_expert_role
from tmis.ai_team.capabilities.mission_templates import template_for
from tmis.ai_team.capabilities.schemas import LegalDomain, TaskType
from tmis.ai_team.planner.schemas import MissionPlan, SubTask, new_subtask_id

_RESEARCH_TASK_TYPES = (TaskType.JURISPRUDENCE_RESEARCH, TaskType.LEGAL_RESEARCH)


class Planner:
    """Decomposes a mission request into an ordered sub-task pipeline
    (see docs/55-guide-coordinateur.md — Planner), built from the same
    `tmis.ai_team.capabilities.mission_templates` registry
    `tmis.ai_team.teams.TeamBuilder` uses to compose a team — so a
    generated plan's roles are always a subset of what a matching
    team actually contains. When the mission's `LegalDomain` calls for
    a specialist (RGPD/fiscal/social), a `RISK_ANALYSIS` sub-task for
    that expert is spliced in right after the last research step."""

    def decompose(
        self, domain: LegalDomain = LegalDomain.GENERAL, *, case_type: str = "full_case_analysis"
    ) -> MissionPlan:
        steps = template_for(case_type)

        sub_tasks: list[SubTask] = []
        previous_id: str | None = None
        last_research_id: str | None = None
        for task_type, role in steps:
            sub_task = SubTask(
                id=new_subtask_id(),
                task_type=task_type,
                assigned_role=role,
                description=_DESCRIPTIONS.get(task_type, task_type.value),
                depends_on=(previous_id,) if previous_id else (),
            )
            sub_tasks.append(sub_task)
            previous_id = sub_task.id
            if task_type in _RESEARCH_TASK_TYPES:
                last_research_id = sub_task.id

        expert_role = domain_expert_role(domain)
        if expert_role is not None and last_research_id is not None:
            sub_tasks = self._splice_after(
                sub_tasks,
                after_id=last_research_id,
                new_sub_task=SubTask(
                    id=new_subtask_id(),
                    task_type=TaskType.RISK_ANALYSIS,
                    assigned_role=expert_role,
                    description=f"Analyser les risques spécifiques au domaine {domain.value}.",
                    depends_on=(last_research_id,),
                ),
            )

        return MissionPlan(sub_tasks=sub_tasks)

    @staticmethod
    def _splice_after(
        sub_tasks: list[SubTask], *, after_id: str, new_sub_task: SubTask
    ) -> list[SubTask]:
        """Inserts `new_sub_task` right after the sub-task with id
        `after_id`, and rewires whichever sub-task used to depend on
        `after_id` to depend on `new_sub_task` instead — so the new
        step is threaded into the chain rather than left dangling."""
        result: list[SubTask] = []
        for sub_task in sub_tasks:
            if after_id in sub_task.depends_on and sub_task.id != new_sub_task.id:
                sub_task = SubTask(
                    id=sub_task.id,
                    task_type=sub_task.task_type,
                    assigned_role=sub_task.assigned_role,
                    description=sub_task.description,
                    depends_on=tuple(
                        new_sub_task.id if dep == after_id else dep for dep in sub_task.depends_on
                    ),
                )
            result.append(sub_task)
            if sub_task.id == after_id:
                result.append(new_sub_task)
        return result


_DESCRIPTIONS: dict[TaskType, str] = {
    TaskType.DOCUMENT_ANALYSIS: "Analyser les documents du dossier.",
    TaskType.LEGAL_RESEARCH: "Rechercher les textes juridiques applicables.",
    TaskType.JURISPRUDENCE_RESEARCH: "Rechercher la jurisprudence pertinente.",
    TaskType.REASONING: "Construire le raisonnement juridique.",
    TaskType.DRAFTING: "Rédiger le document à partir du raisonnement établi.",
    TaskType.VERIFICATION: "Vérifier la fiabilité et la cohérence du contenu.",
    TaskType.QUALITY_CONTROL: "Contrôler la qualité finale du livrable.",
}
