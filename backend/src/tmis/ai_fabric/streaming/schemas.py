from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StreamChunk:
    text: str
    is_final: bool = False
