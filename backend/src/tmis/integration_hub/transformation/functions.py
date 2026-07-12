from datetime import datetime

from tmis.integration_hub.transformation.schemas import TransformKind

_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")


class UppercaseTransform:
    kind = TransformKind.UPPERCASE

    def apply(self, value: str) -> str:
        return value.upper()


class LowercaseTransform:
    kind = TransformKind.LOWERCASE

    def apply(self, value: str) -> str:
        return value.lower()


class TrimTransform:
    kind = TransformKind.TRIM

    def apply(self, value: str) -> str:
        return value.strip()


class DateIsoTransform:
    """Normalizes a handful of common external date formats to ISO
    8601; unparseable values pass through unchanged rather than
    raising, since a malformed source value should not abort a sync."""

    kind = TransformKind.DATE_ISO

    def apply(self, value: str) -> str:
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date().isoformat()
            except ValueError:
                continue
        return value


def default_transforms() -> tuple[
    UppercaseTransform, LowercaseTransform, TrimTransform, DateIsoTransform
]:
    return (UppercaseTransform(), LowercaseTransform(), TrimTransform(), DateIsoTransform())
