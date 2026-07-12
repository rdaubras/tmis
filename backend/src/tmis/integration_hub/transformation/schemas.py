from enum import StrEnum


class TransformKind(StrEnum):
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    TRIM = "trim"
    DATE_ISO = "date_iso"
