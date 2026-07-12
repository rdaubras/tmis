from fastapi.testclient import TestClient

from tmis.main import app


def test_submit_and_list_runtime_tasks() -> None:
    client = TestClient(app)
    submitted = client.post(
        "/runtime/tasks", params={"task_id": "task-api-1", "name": "demo", "priority": 3}
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "pending"

    ready = client.get("/runtime/tasks/ready")
    assert ready.status_code == 200
    assert any(t["id"] == "task-api-1" for t in ready.json())

    cancelled = client.post("/runtime/tasks/task-api-1/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["cancelled"] is True


def test_enqueue_job_and_read_dead_letters() -> None:
    client = TestClient(app)
    enqueued = client.post(
        "/runtime/jobs", params={"queue_name": "demo-queue", "max_attempts": 0}
    )
    assert enqueued.status_code == 200
    job_id = enqueued.json()["id"]

    failed = client.post(f"/runtime/jobs/{job_id}/fail", params={"error": "boom"})
    assert failed.status_code == 200
    assert failed.json()["status"] == "dead_lettered"

    dead_letters = client.get("/runtime/jobs/dead-letters", params={"queue_name": "demo-queue"})
    assert dead_letters.status_code == 200
    assert any(j["id"] == job_id for j in dead_letters.json())


def test_workflow_event_replay_and_archive() -> None:
    client = TestClient(app)
    before = client.get("/runtime/events/workflow/replay")
    assert before.status_code == 200

    archived = client.post("/runtime/events/workflow/archive", params={"before_sequence": 0})
    assert archived.status_code == 200
    assert archived.json()["archived_count"] == 0


def test_cache_stats_endpoint_returns_counters() -> None:
    client = TestClient(app)
    response = client.get("/runtime/cache/stats")
    assert response.status_code == 200
    body = response.json()
    assert "hits" in body
    assert "misses" in body


def test_event_store_append_replay_snapshot_archive_restore() -> None:
    client = TestClient(app)
    appended = client.post(
        "/runtime/event-store/stream-api-1/events",
        params={"event_type": "Created"},
        json={"name": "Acme"},
    )
    assert appended.status_code == 200
    assert appended.json()["sequence"] == 1

    replayed = client.get("/runtime/event-store/stream-api-1/replay")
    assert replayed.status_code == 200
    assert len(replayed.json()) == 1

    snapshot = client.post(
        "/runtime/event-store/stream-api-1/snapshot", json={"name": "Acme"}
    )
    assert snapshot.status_code == 200
    assert snapshot.json()["version"] == 1

    archived = client.post("/runtime/event-store/stream-api-1/archive")
    assert archived.status_code == 200
    assert archived.json()["archived"] is True

    blocked = client.post(
        "/runtime/event-store/stream-api-1/events",
        params={"event_type": "Blocked"},
        json={},
    )
    assert blocked.status_code == 409

    restored = client.post("/runtime/event-store/stream-api-1/restore")
    assert restored.status_code == 200
    assert restored.json()["archived"] is False


def test_optimizer_recommendations_endpoint_returns_a_list() -> None:
    client = TestClient(app)
    response = client.get("/runtime/optimizer/recommendations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_ha_heartbeat_supervise_and_failover() -> None:
    client = TestClient(app)
    beat = client.post("/runtime/ha/heartbeat/node-api-1")
    assert beat.status_code == 200
    assert beat.json()["status"] == "healthy"

    supervise = client.get("/runtime/ha/supervise")
    assert supervise.status_code == 200
    assert supervise.json()["node-api-1"] == "healthy"

    failover = client.get("/runtime/ha/failover/node-api-1")
    assert failover.status_code == 200
    assert failover.json()["should_failover"] is False


def test_disaster_recovery_policy_and_rpo_rto() -> None:
    client = TestClient(app)
    policy = client.post(
        "/runtime/disaster-recovery/policy/firm-api-1",
        params={"schedule_cron": "0 3 * * *", "retention_days": 30},
    )
    assert policy.status_code == 200
    assert policy.json()["retention_days"] == 30

    estimate = client.get("/runtime/disaster-recovery/rpo-rto")
    assert estimate.status_code == 200
    assert estimate.json()["meets_objective"] is False


def test_autoscaling_recommend_and_bottlenecks() -> None:
    client = TestClient(app)
    missing = client.get(
        "/runtime/autoscaling/recommend/queue_depth", params={"current_replicas": 2}
    )
    assert missing.status_code == 200
    assert missing.json() is None

    bottlenecks = client.get("/runtime/autoscaling/bottlenecks")
    assert bottlenecks.status_code == 200
    assert isinstance(bottlenecks.json(), list)


def test_load_test_endpoint_runs_small_preset() -> None:
    client = TestClient(app)
    response = client.post("/runtime/load-test/100")
    assert response.status_code == 200
    body = response.json()
    assert body["concurrent_users"] == 100
    assert body["total_requests"] == 100


def test_chaos_scenario_run_probe_and_recover() -> None:
    client = TestClient(app)
    run = client.post("/runtime/chaos/cache_loss")
    assert run.status_code == 200
    assert run.json()["dependency"] == "runtime_platform.cache"

    probe = client.post("/runtime/chaos/cache_loss/probe")
    assert probe.status_code == 200
    assert probe.json()["available"] is False

    conflict = client.post("/runtime/chaos/cache_loss/recover")
    assert conflict.status_code == 409
