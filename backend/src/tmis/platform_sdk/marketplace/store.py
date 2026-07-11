from tmis.platform_sdk.marketplace.schemas import Review


class InMemoryReviewStore:
    def __init__(self) -> None:
        self._reviews: list[Review] = []

    def save(self, review: Review) -> None:
        self._reviews.append(review)

    def list_for_plugin(self, plugin_id: str) -> list[Review]:
        return [r for r in self._reviews if r.plugin_id == plugin_id]
