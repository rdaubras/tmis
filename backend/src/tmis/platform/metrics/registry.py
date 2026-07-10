"""A minimal, dependency-free metrics registry with a hand-rolled
Prometheus text-exposition-format renderer.

TMIS has no metrics-client dependency yet. Rather than add one for a
mock-scope `/metrics` endpoint, this writes the small, well-documented
Prometheus text format by hand — the same "hand-roll it, no new
dependency" choice already made for the PDF writer
(`tmis.legal_drafting.export.pdf_writer`) and the XLSX writer
(`tmis.cabinet_os.reports.xlsx_writer`). See
docs/49-guide-supervision.md.
"""

from collections import defaultdict
from typing import TypeVar

LabelKey = tuple[tuple[str, str], ...]
_MetricT = TypeVar("_MetricT", "Counter", "Gauge", "Histogram")

_DEFAULT_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


def _label_key(labels: dict[str, str]) -> LabelKey:
    return tuple(sorted(labels.items()))


def _format_labels(key: LabelKey) -> str:
    if not key:
        return ""
    return "{" + ",".join(f'{name}="{value}"' for name, value in key) + "}"


class Counter:
    """A value that only increases (see docs/49-guide-supervision.md
    — Métriques): request counts, error counts, tokens consumed..."""

    def __init__(self, name: str, help_text: str) -> None:
        self.name = name
        self.help_text = help_text
        self._values: dict[LabelKey, float] = defaultdict(float)

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        self._values[_label_key(labels)] += amount

    def total(self) -> float:
        """The sum across every label combination — for structured
        dashboards that want one number, not a label breakdown (see
        `tmis.platform.monitoring`)."""
        return sum(self._values.values())

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} counter"]
        for key, value in self._values.items():
            lines.append(f"{self.name}{_format_labels(key)} {value}")
        return "\n".join(lines)


class Gauge:
    """A value that can go up or down: active connections, queue
    depth, storage used..."""

    def __init__(self, name: str, help_text: str) -> None:
        self.name = name
        self.help_text = help_text
        self._values: dict[LabelKey, float] = defaultdict(float)

    def set(self, value: float, **labels: str) -> None:
        self._values[_label_key(labels)] = value

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        self._values[_label_key(labels)] += amount

    def dec(self, amount: float = 1.0, **labels: str) -> None:
        self._values[_label_key(labels)] -= amount

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} gauge"]
        for key, value in self._values.items():
            lines.append(f"{self.name}{_format_labels(key)} {value}")
        return "\n".join(lines)


class Histogram:
    """Observation counts bucketed by upper bound — request latency,
    document size, token counts... `render()` follows the standard
    Prometheus histogram shape (`_bucket`/`_sum`/`_count`)."""

    def __init__(
        self, name: str, help_text: str, buckets: tuple[float, ...] = _DEFAULT_LATENCY_BUCKETS
    ) -> None:
        self.name = name
        self.help_text = help_text
        self._buckets = tuple(sorted(buckets))
        self._bucket_counts: dict[LabelKey, list[int]] = {}
        self._sums: dict[LabelKey, float] = defaultdict(float)
        self._counts: dict[LabelKey, int] = defaultdict(int)

    def observe(self, value: float, **labels: str) -> None:
        """Increments only the *first* bucket the value qualifies for
        — `render()` performs the cumulative sum across buckets that
        gives the standard Prometheus "count of observations <= le"
        semantics. Incrementing every qualifying bucket here *and*
        cumulating again in `render()` would double-count."""
        key = _label_key(labels)
        if key not in self._bucket_counts:
            self._bucket_counts[key] = [0] * len(self._buckets)
        for index, upper_bound in enumerate(self._buckets):
            if value <= upper_bound:
                self._bucket_counts[key][index] += 1
                break
        self._sums[key] += value
        self._counts[key] += 1

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} histogram"]
        for key, counts in self._bucket_counts.items():
            base_labels = dict(key)
            cumulative = 0
            for upper_bound, bucket_count in zip(self._buckets, counts, strict=True):
                cumulative += bucket_count
                bucket_labels = _format_labels(
                    _label_key({**base_labels, "le": str(upper_bound)})
                )
                lines.append(f"{self.name}_bucket{bucket_labels} {cumulative}")
            inf_labels = _format_labels(_label_key({**base_labels, "le": "+Inf"}))
            lines.append(f"{self.name}_bucket{inf_labels} {self._counts[key]}")
            lines.append(f"{self.name}_sum{_format_labels(key)} {self._sums[key]}")
            lines.append(f"{self.name}_count{_format_labels(key)} {self._counts[key]}")
        return "\n".join(lines)


class MetricsRegistry:
    """Holds every metric TMIS exposes and renders them all in
    Prometheus text-exposition format for a `/metrics` endpoint (see
    docs/49-guide-supervision.md)."""

    def __init__(self) -> None:
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}

    def counter(self, name: str, help_text: str) -> Counter:
        return self._get_or_create(name, Counter(name, help_text))

    def gauge(self, name: str, help_text: str) -> Gauge:
        return self._get_or_create(name, Gauge(name, help_text))

    def histogram(
        self, name: str, help_text: str, buckets: tuple[float, ...] = _DEFAULT_LATENCY_BUCKETS
    ) -> Histogram:
        return self._get_or_create(name, Histogram(name, help_text, buckets))

    def render(self) -> str:
        return "\n".join(metric.render() for metric in self._metrics.values()) + "\n"

    def try_get(self, name: str) -> "Counter | Gauge | Histogram | None":
        """Looks up an already-registered metric by name without
        creating one — for read-only consumers (dashboards) that must
        not accidentally register a metric no one ever observes."""
        return self._metrics.get(name)

    def _get_or_create(self, name: str, fresh_metric: _MetricT) -> _MetricT:
        existing = self._metrics.get(name)
        if existing is None:
            self._metrics[name] = fresh_metric
            return fresh_metric
        if not isinstance(existing, type(fresh_metric)):
            raise TypeError(f"Metric {name!r} is already registered with a different type")
        return existing
