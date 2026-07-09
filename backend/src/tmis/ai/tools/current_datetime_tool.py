from datetime import UTC, datetime


class CurrentDatetimeTool:
    """Example tool proving the `ToolRegistry` mechanism; not a business
    feature (see docs/09-roadmap-30-sprints.md)."""

    name = "current_datetime"
    description = "Returns the current UTC date and time in ISO 8601 format."

    async def run(self, **kwargs: object) -> object:
        return datetime.now(UTC).isoformat()
