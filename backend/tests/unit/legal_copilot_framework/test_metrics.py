import pytest

from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.legal_copilot_framework.metrics.engine import CopilotMetricsEngine
from tmis.platform.metrics.registry import MetricsRegistry

FIRM = "firm-a"
COPILOT = "copilot-contentieux"


def _engine() -> CopilotMetricsEngine:
    return CopilotMetricsEngine(MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry()))


def test_snapshot_of_unused_copilot_is_all_zero() -> None:
    engine = _engine()
    snapshot = engine.snapshot(COPILOT, firm_id=FIRM)

    assert snapshot.copilot_id == COPILOT
    assert snapshot.usage_count == 0
    assert snapshot.total_ai_cost_usd == 0.0
    assert snapshot.avg_response_time_ms == 0.0
    assert snapshot.validation_rate == 0.0
    assert snapshot.pack_reuse_count == 0
    assert snapshot.satisfaction_score is None


def test_snapshot_aggregates_recorded_events() -> None:
    engine = _engine()
    engine.record_usage(COPILOT, firm_id=FIRM)
    engine.record_usage(COPILOT, firm_id=FIRM)
    engine.record_cost(COPILOT, 0.10, firm_id=FIRM)
    engine.record_cost(COPILOT, 0.20, firm_id=FIRM)
    engine.record_response_time(COPILOT, 400.0, firm_id=FIRM)
    engine.record_response_time(COPILOT, 600.0, firm_id=FIRM)
    engine.record_validation(COPILOT, True, firm_id=FIRM)
    engine.record_validation(COPILOT, False, firm_id=FIRM)
    engine.record_pack_reuse(COPILOT, firm_id=FIRM)

    snapshot = engine.snapshot(COPILOT, firm_id=FIRM)

    assert snapshot.usage_count == 2
    assert snapshot.total_ai_cost_usd == pytest.approx(0.30)
    assert snapshot.avg_response_time_ms == 500.0
    assert snapshot.validation_rate == 0.5
    assert snapshot.pack_reuse_count == 1


def test_satisfaction_score_stays_none_unless_recorded() -> None:
    engine = _engine()
    engine.record_usage(COPILOT, firm_id=FIRM)

    assert engine.snapshot(COPILOT, firm_id=FIRM).satisfaction_score is None

    engine.record_satisfaction(COPILOT, 0.9, firm_id=FIRM)

    assert engine.snapshot(COPILOT, firm_id=FIRM).satisfaction_score == 0.9


def test_snapshot_is_scoped_per_copilot() -> None:
    engine = _engine()
    engine.record_usage(COPILOT, firm_id=FIRM)
    engine.record_usage("copilot-contrats", firm_id=FIRM)

    assert engine.snapshot(COPILOT, firm_id=FIRM).usage_count == 1
    assert engine.snapshot("copilot-contrats", firm_id=FIRM).usage_count == 1
