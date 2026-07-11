from typing import Protocol

from tmis.ai_governance.bias_detection.schemas import BiasFinding


class BiasDetectorPort(Protocol):
    """One pluggable bias detector. `BiasDetectionEngine` is
    deliberately closed over this single narrow contract so a new
    detector can be registered without any change to the engine — the
    sprint's explicit "moteur extensible" requirement."""

    name: str

    def detect(self, text: str) -> list[BiasFinding]: ...
