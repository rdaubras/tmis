from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.capabilities.schemas import LegalDomain, TaskType
from tmis.ai_team.planner.engine import Planner


def test_full_plan_follows_the_sprint_pipeline_order() -> None:
    plan = Planner().decompose(LegalDomain.GENERAL, case_type="full_case_analysis")

    task_types = [st.task_type for st in plan.sub_tasks]
    assert task_types == [
        TaskType.DOCUMENT_ANALYSIS,
        TaskType.LEGAL_RESEARCH,
        TaskType.JURISPRUDENCE_RESEARCH,
        TaskType.REASONING,
        TaskType.DRAFTING,
        TaskType.VERIFICATION,
        TaskType.QUALITY_CONTROL,
    ]


def test_full_plan_chains_dependencies_linearly() -> None:
    plan = Planner().decompose(LegalDomain.GENERAL, case_type="full_case_analysis")

    for previous, current in zip(plan.sub_tasks, plan.sub_tasks[1:], strict=False):
        assert current.depends_on == (previous.id,)
    assert plan.sub_tasks[0].depends_on == ()


def test_domain_expert_step_is_spliced_in_after_research() -> None:
    plan = Planner().decompose(LegalDomain.DATA_PROTECTION, case_type="full_case_analysis")

    risk_steps = [st for st in plan.sub_tasks if st.task_type is TaskType.RISK_ANALYSIS]
    assert len(risk_steps) == 1
    assert risk_steps[0].assigned_role is AgentRole.GDPR_EXPERT

    jurisprudence_step = next(
        st for st in plan.sub_tasks if st.task_type is TaskType.JURISPRUDENCE_RESEARCH
    )
    assert risk_steps[0].depends_on == (jurisprudence_step.id,)

    reasoning_step = next(st for st in plan.sub_tasks if st.task_type is TaskType.REASONING)
    assert reasoning_step.depends_on == (risk_steps[0].id,)


def test_general_domain_never_gets_a_risk_analysis_step() -> None:
    plan = Planner().decompose(LegalDomain.GENERAL, case_type="full_case_analysis")

    assert not any(st.task_type is TaskType.RISK_ANALYSIS for st in plan.sub_tasks)


def test_quick_review_is_a_two_step_plan() -> None:
    plan = Planner().decompose(case_type="quick_review")

    assert len(plan.sub_tasks) == 2
    assert plan.sub_tasks[0].task_type is TaskType.VERIFICATION
    assert plan.sub_tasks[1].depends_on == (plan.sub_tasks[0].id,)


def test_unknown_case_type_falls_back_to_full_case_analysis() -> None:
    plan = Planner().decompose(case_type="not-a-real-case-type")

    assert len(plan.sub_tasks) == 7
