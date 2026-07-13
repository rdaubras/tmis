from tmis.cloud_operations.alerting.ports import AlertEventStorePort, AlertRuleStorePort
from tmis.cloud_operations.alerting.schemas import (
    AlertComparison,
    AlertEvent,
    AlertRule,
    AlertSeverity,
    new_alert_event_id,
    new_alert_rule_id,
)
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.notifications.schemas import NotificationChannel


class UnknownAlertRuleError(KeyError):
    pass


def _breaches(comparison: AlertComparison, observed: float, threshold: float) -> bool:
    if comparison is AlertComparison.GREATER_THAN:
        return observed > threshold
    return observed < threshold


class AlertingEngine:
    """Evaluates configurable thresholds (sprint examples: "augmentation
    du temps de réponse, taux d'erreur élevé, échec d'un workflow
    critique, indisponibilité d'un fournisseur IA, dépassement des
    quotas") against `cloud_operations.metrics.MetricsEngine` history.
    Delivery composes `collaboration.notifications.NotificationEngine`
    (Sprint 8) directly — the only notification-channel engine in
    TMIS — rather than building a second one; `firm_id` is passed as
    `workspace_id`, the same convention `business_platform.
    notifications.BusinessNotificationEngine` already documents.
    Platform-wide rules (`firm_id=None`) are recorded and queryable
    but never dispatched through a firm's notification channel — there
    is no firm to notify."""

    def __init__(
        self,
        rules: AlertRuleStorePort,
        events: AlertEventStorePort,
        metrics: MetricsEngine,
        notifications: NotificationEngine | None = None,
    ) -> None:
        self._rules = rules
        self._events = events
        self._metrics = metrics
        self._notifications = notifications

    def configure_rule(
        self,
        name: str,
        category: MetricCategory,
        comparison: AlertComparison,
        threshold: float,
        *,
        severity: AlertSeverity = AlertSeverity.WARNING,
        firm_id: str | None = None,
        notify_recipient_id: str | None = None,
    ) -> AlertRule:
        rule = AlertRule(
            id=new_alert_rule_id(),
            name=name,
            category=category,
            comparison=comparison,
            threshold=threshold,
            severity=severity,
            firm_id=firm_id,
            notify_recipient_id=notify_recipient_id,
        )
        self._rules.save(rule)
        return rule

    def deactivate_rule(self, rule_id: str) -> AlertRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise UnknownAlertRuleError(rule_id)
        rule.active = False
        self._rules.save(rule)
        return rule

    def evaluate(self, rule_id: str) -> AlertEvent | None:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise UnknownAlertRuleError(rule_id)
        history = self._metrics.history_for_category(rule.category, rule.firm_id)
        if not history:
            return None
        observed_value = history[-1].value
        if not _breaches(rule.comparison, observed_value, rule.threshold):
            return None
        event = AlertEvent(
            id=new_alert_event_id(),
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            observed_value=observed_value,
            threshold=rule.threshold,
            firm_id=rule.firm_id,
        )
        self._events.save(event)
        self._notify(rule, event)
        return event

    def evaluate_all(self, firm_id: str | None = None) -> list[AlertEvent]:
        fired = []
        for rule in self._rules.list_active(firm_id):
            event = self.evaluate(rule.id)
            if event is not None:
                fired.append(event)
        return fired

    def history(self, firm_id: str | None = None) -> list[AlertEvent]:
        return self._events.list_for_firm(firm_id) if firm_id else self._events.list_all()

    def _notify(self, rule: AlertRule, event: AlertEvent) -> None:
        if self._notifications is None or rule.firm_id is None or rule.notify_recipient_id is None:
            return
        self._notifications.dispatch(
            workspace_id=rule.firm_id,
            recipient_id=rule.notify_recipient_id,
            notification_type="cloud_operations.alert",
            payload={
                "rule_name": rule.name,
                "severity": event.severity.value,
                "observed_value": str(event.observed_value),
                "threshold": str(event.threshold),
            },
            channels=[NotificationChannel.IN_APP],
        )
