from tmis.ai_governance.bias_detection.detectors import GeneralizationBiasDetector
from tmis.ai_governance.bias_detection.ports import BiasDetectorPort
from tmis.ai_governance.bias_detection.schemas import BiasFinding


class BiasDetectionEngine:
    """The sprint's "BIAS DETECTION": runs every registered
    `BiasDetectorPort` over a text and collects their findings. Seeded
    with `GeneralizationBiasDetector` by default; `register()` adds a
    new detector at runtime, satisfying the sprint's "moteur
    extensible" requirement without ever modifying this class."""

    def __init__(self, detectors: list[BiasDetectorPort] | None = None) -> None:
        self._detectors: list[BiasDetectorPort] = (
            list(detectors) if detectors is not None else [GeneralizationBiasDetector()]
        )

    def register(self, detector: BiasDetectorPort) -> None:
        self._detectors.append(detector)

    def scan(self, text: str) -> list[BiasFinding]:
        findings: list[BiasFinding] = []
        for detector in self._detectors:
            findings.extend(detector.detect(text))
        return findings
