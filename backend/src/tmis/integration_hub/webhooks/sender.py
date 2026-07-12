import structlog

from tmis.integration_hub.webhooks.schemas import WebhookDeliveryResult

_logger = structlog.get_logger(__name__)


class LoggingWebhookSender:
    """Reference `WebhookSenderPort` implementation: logs the outbound
    delivery instead of performing a real HTTP call — replaceable by
    an httpx-based sender wired at bootstrap time without touching
    `WebhookEngine`."""

    async def send(
        self, url: str, payload: dict[str, str], headers: dict[str, str]
    ) -> WebhookDeliveryResult:
        _logger.info("integration_hub.webhook_dispatch", url=url, payload=payload)
        return WebhookDeliveryResult(success=True, status_code=200, detail="logged, not sent")
