from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueStats:
    """Snapshot of the five measures the sprint asks for ("taille,
    débit, temps d'attente, erreurs, retries") for one named queue."""

    queue_name: str
    size: int
    processed: int
    errors: int
    retries: int
    average_wait_ms: float
