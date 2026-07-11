from tmis.strategic_intelligence.timeline.schemas import StrategicTimelineEntry


class TimelineEngine:
    """Merges facts, events, deadlines and proposed actions into a
    single sorted, visualization-ready chronology."""

    def build(
        self, entries: list[StrategicTimelineEntry]
    ) -> list[StrategicTimelineEntry]:
        return sorted(entries, key=lambda e: e.date)
