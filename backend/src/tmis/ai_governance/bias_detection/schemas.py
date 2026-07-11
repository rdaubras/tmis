import uuid
from dataclasses import dataclass


def new_bias_finding_id() -> str:
    return f"bias-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class BiasFinding:
    """A single detected bias — always carries `explanation`, never a
    bare flag. `category` is a free-form string (not a closed enum) so
    a new detector can introduce a new category without editing this
    module."""

    id: str
    detector_name: str
    category: str
    excerpt: str
    description: str
    explanation: str
