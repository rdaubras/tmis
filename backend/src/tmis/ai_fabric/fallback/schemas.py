class NoAvailableModelError(Exception):
    """Raised when neither the primary model nor any of its
    configured fallbacks is available — the caller (the router) must
    surface this rather than silently returning a degraded result."""

    def __init__(self, attempted_model_names: tuple[str, ...]) -> None:
        super().__init__(f"No available model among: {', '.join(attempted_model_names)}")
        self.attempted_model_names = attempted_model_names
