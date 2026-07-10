import pytest

from tmis.platform.metrics.registry import Counter, Gauge, Histogram, MetricsRegistry


def test_counter_accumulates_across_labels() -> None:
    counter = Counter("requests_total", "total requests")
    counter.inc(method="GET")
    counter.inc(method="GET")
    counter.inc(method="POST")

    assert counter.total() == 3


def test_counter_render_includes_help_and_type_lines() -> None:
    counter = Counter("requests_total", "total requests")
    counter.inc()

    rendered = counter.render()

    assert "# HELP requests_total total requests" in rendered
    assert "# TYPE requests_total counter" in rendered


def test_gauge_set_inc_dec() -> None:
    gauge = Gauge("queue_depth", "items in queue")
    gauge.set(10, queue="default")
    gauge.inc(5, queue="default")
    gauge.dec(2, queue="default")

    rendered = gauge.render()

    assert 'queue_depth{queue="default"} 13' in rendered


def test_histogram_bucket_counts_are_not_double_counted() -> None:
    """Regression test: `observe()` must increment only the first
    qualifying bucket, letting `render()`'s cumulative sum be the sole
    source of the standard Prometheus "count of observations <= le"
    semantics. A prior bug incremented every qualifying bucket at
    observe-time *and* cumulated again at render-time, multiplying
    bucket counts far beyond the true observation count."""
    histogram = Histogram("latency_seconds", "latency", buckets=(0.1, 1.0, 10.0))
    histogram.observe(0.02)
    histogram.observe(0.3)

    rendered = histogram.render()

    assert 'latency_seconds_bucket{le="0.1"} 1' in rendered
    assert 'latency_seconds_bucket{le="1.0"} 2' in rendered
    assert 'latency_seconds_bucket{le="10.0"} 2' in rendered
    assert "latency_seconds_count 2" in rendered
    assert "latency_seconds_sum 0.32" in rendered


def test_histogram_value_beyond_every_bucket_only_counts_in_inf() -> None:
    histogram = Histogram("size_bytes", "size", buckets=(10.0, 20.0))
    histogram.observe(1000.0)

    rendered = histogram.render()

    assert 'size_bytes_bucket{le="10.0"} 0' in rendered
    assert 'size_bytes_bucket{le="20.0"} 0' in rendered
    assert 'size_bytes_bucket{le="+Inf"} 1' in rendered


def test_metrics_registry_returns_the_same_instance_for_a_repeated_name() -> None:
    registry = MetricsRegistry()
    first = registry.counter("http_requests_total", "total")
    second = registry.counter("http_requests_total", "total")

    assert first is second


def test_metrics_registry_rejects_type_mismatch_for_an_existing_name() -> None:
    registry = MetricsRegistry()
    registry.counter("thing", "a thing")

    with pytest.raises(TypeError):
        registry.gauge("thing", "a thing")


def test_metrics_registry_try_get_does_not_create() -> None:
    registry = MetricsRegistry()

    assert registry.try_get("never_registered") is None


def test_metrics_registry_render_combines_every_metric() -> None:
    registry = MetricsRegistry()
    registry.counter("a_total", "a").inc()
    registry.gauge("b_gauge", "b").set(5)

    rendered = registry.render()

    assert "a_total" in rendered
    assert "b_gauge" in rendered
