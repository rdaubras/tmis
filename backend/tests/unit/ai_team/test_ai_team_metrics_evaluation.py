from tmis.ai_team.evaluation.engine import MissionQualityScorer
from tmis.ai_team.metrics.engine import MetricsCollector


def test_summary_aggregates_cost_and_duration() -> None:
    collector = MetricsCollector()
    collector.record_agent_run("m1", "st-1", "agent-1", 1.5, 0.02, 0.8)
    collector.record_agent_run("m1", "st-2", "agent-2", 2.5, 0.03, 0.9)

    summary = collector.summary_for_mission("m1")

    assert summary.agent_runs == 2
    assert summary.total_cost_usd == 0.05
    assert summary.total_duration_seconds == 4.0


def test_consensus_rate_defaults_to_one_without_checks() -> None:
    collector = MetricsCollector()

    summary = collector.summary_for_mission("m1")

    assert summary.consensus_rate == 1.0


def test_consensus_rate_reflects_resolved_ratio() -> None:
    collector = MetricsCollector()
    collector.record_consensus("m1", resolved=True)
    collector.record_consensus("m1", resolved=False)

    summary = collector.summary_for_mission("m1")

    assert summary.consensus_rate == 0.5


def test_revision_and_human_validation_counts() -> None:
    collector = MetricsCollector()
    collector.record_revision("m1")
    collector.record_revision("m1")
    collector.record_human_validation("m1")

    summary = collector.summary_for_mission("m1")

    assert summary.revision_count == 2
    assert summary.human_validation_count == 1


def test_metrics_are_scoped_per_mission() -> None:
    collector = MetricsCollector()
    collector.record_agent_run("m1", "st-1", "agent-1", 1.0, 0.01, 0.8)
    collector.record_agent_run("m2", "st-1", "agent-1", 1.0, 0.01, 0.8)

    assert collector.summary_for_mission("m1").agent_runs == 1
    assert len(collector.all_agent_runs()) == 2


def test_evaluator_scores_perfect_run_at_full_quality() -> None:
    collector = MetricsCollector()
    summary = collector.summary_for_mission("m1")

    evaluation = MissionQualityScorer().evaluate_mission(
        "m1", average_agent_quality=0.9, metrics=summary
    )

    assert evaluation.overall_quality_score == 0.9
    assert "Aucune validation humaine" in evaluation.notes[0]


def test_evaluator_penalizes_revisions() -> None:
    collector = MetricsCollector()
    collector.record_revision("m1")
    collector.record_revision("m1")
    summary = collector.summary_for_mission("m1")

    evaluation = MissionQualityScorer().evaluate_mission(
        "m1", average_agent_quality=0.9, metrics=summary
    )

    assert evaluation.overall_quality_score < 0.9
    assert any("révision" in note for note in evaluation.notes)


def test_evaluator_penalizes_low_consensus() -> None:
    collector = MetricsCollector()
    collector.record_consensus("m1", resolved=False)
    summary = collector.summary_for_mission("m1")

    evaluation = MissionQualityScorer().evaluate_mission(
        "m1", average_agent_quality=1.0, metrics=summary
    )

    assert evaluation.overall_quality_score < 1.0
    assert any("Désaccord" in note for note in evaluation.notes)


def test_evaluator_score_never_goes_negative() -> None:
    collector = MetricsCollector()
    for _ in range(10):
        collector.record_revision("m1")
    summary = collector.summary_for_mission("m1")

    evaluation = MissionQualityScorer().evaluate_mission(
        "m1", average_agent_quality=0.1, metrics=summary
    )

    assert evaluation.overall_quality_score >= 0.0
