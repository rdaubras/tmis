from tmis.integration_hub.transformation.functions import default_transforms
from tmis.integration_hub.transformation.ports import TransformFunctionPort
from tmis.integration_hub.transformation.schemas import TransformKind


class UnknownTransformError(KeyError):
    pass


class TransformationEngine:
    """Registry of pluggable value transforms — same
    register()-without-touching-the-engine extensibility pattern as
    `authentication.AuthenticationEngine`."""

    def __init__(self, functions: dict[TransformKind, TransformFunctionPort] | None = None) -> None:
        self._functions: dict[TransformKind, TransformFunctionPort] = functions or {
            f.kind: f for f in default_transforms()
        }

    def register(self, function: TransformFunctionPort) -> None:
        self._functions[function.kind] = function

    def apply(self, transform_id: str, value: str) -> str:
        kind = TransformKind(transform_id)
        fn = self._functions.get(kind)
        if fn is None:
            raise UnknownTransformError(transform_id)
        return fn.apply(value)
