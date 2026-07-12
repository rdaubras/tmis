"""Demonstrates the Legal Integration Hub (LIH) end to end: connector
registration, configurable field mapping, a synchronization run that
detects and resolves a conflict via human validation, and a signed
inbound webhook bridged into `workflow_automation`'s event bus.

Run from `backend/`: `python -m scripts.demo_integration_hub`

Uses a separate fictional firm (`firm-demo-lih` / "Cabinet Démo
Lefèvre & Associés — Intégrations") so it never touches data from
other demo scripts. Every store is the in-memory reference
implementation, so this is safe to re-run freely.
"""

import asyncio
import json
from datetime import UTC, datetime

from tmis.ai_governance.bootstrap import get_human_validation_engine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.integration_hub.bootstrap import (
    get_conflict_resolution_engine,
    get_connector_registry_engine,
    get_event_bridge,
    get_health_check_engine,
    get_integration_event_bus,
    get_mapping_engine,
    get_mapping_profile_store,
    get_synchronization_engine,
)
from tmis.integration_hub.conflict_resolution import ConflictStrategy
from tmis.integration_hub.conflict_resolution.strategies import HumanValidationStrategy
from tmis.integration_hub.connector_framework import ConnectorRecord
from tmis.integration_hub.event_bridge.schemas import EventDirection
from tmis.integration_hub.mapping import ConnectorMapper, FieldMapping, MappingProfile
from tmis.integration_hub.synchronization import SyncDirection, SyncJobConfig, SyncMode
from tmis.integration_hub.webhooks import (
    InMemoryWebhookSubscriptionStore,
    LoggingWebhookSender,
    WebhookEngine,
    WebhookSubscription,
    sign_payload,
)
from tmis.workflow_automation.bootstrap import get_workflow_event_bus
from tmis.workflow_automation.event_bus import IntegrationEventReceived

FIRM_ID = "firm-demo-lih"
FIRM_NAME = "Cabinet Démo Lefèvre & Associés — Intégrations"


def _print_section(title: str) -> None:
    print(f"\n--- {title} ---")


async def demo_connectors_and_health() -> None:
    _print_section("1. Connecteurs de référence installés")
    registry = get_connector_registry_engine()
    for descriptor in registry.list_connectors():
        print(f"  {descriptor.id:<20} {descriptor.name:<32} statut={descriptor.status.value}")

    health = get_health_check_engine()
    result = health.readiness()
    print(f"Santé globale : {result.status.value} ({len(result.components)} connecteur(s))")


async def demo_sync_with_mapping_and_conflict() -> None:
    _print_section("2. Synchronisation CRM avec mapping et conflit")

    get_mapping_profile_store().save(
        MappingProfile(
            id="mp-demo",
            connector_id="crm-demo",
            firm_id=FIRM_ID,
            entity_type="client",
            fields=(
                FieldMapping(source_field="name", target_field="name", transform_id="uppercase"),
                FieldMapping(source_field="segment", target_field="segment"),
            ),
        )
    )
    mapper = ConnectorMapper(get_mapping_engine(), connector_id="crm-demo", firm_id=FIRM_ID)

    human_validation_engine = get_human_validation_engine()
    conflict_engine = get_conflict_resolution_engine()
    conflict_engine.register(
        HumanValidationStrategy(human_validation_engine, ("associe-demo",))
    )

    class _LocalLookup:
        def find(self, firm_id: str, entity_type: str, external_id: str) -> ConnectorRecord | None:
            return ConnectorRecord(
                external_id="cli-1", data={"name": "SOCIÉTÉ DUPONT SARL (ancien)", "segment": "SME"}
            )

    registry = get_connector_registry_engine()
    connector = registry.get_implementation("crm-demo")

    job = SyncJobConfig(
        id="job-demo-1", connector_id="crm-demo", firm_id=FIRM_ID, entity_type="client",
        direction=SyncDirection.PULL, mode=SyncMode.FULL,
        conflict_strategy=ConflictStrategy.HUMAN_VALIDATION,
    )
    sync_engine = get_synchronization_engine()

    local_lookup = _LocalLookup()
    report = await sync_engine.run_pull(
        job, connector, {}, mapper=mapper, local_lookup=local_lookup
    )
    print(
        f"1re synchronisation : lus={report.result.records_read} "
        f"écrits={report.result.records_written} conflits={report.result.conflicts} "
        f"en attente de validation={report.conflicts_pending_validation}"
    )

    requests = human_validation_engine.history(FIRM_ID, "crm-demo:cli-1")
    if requests:
        human_validation_engine.decide(
            FIRM_ID, requests[0].id, "associe-demo", ValidationDecisionType.APPROVE
        )
        print("Conflit validé par un associé.")

    report2 = await sync_engine.run_pull(
        job, connector, {}, mapper=mapper, local_lookup=local_lookup
    )
    print(
        f"2e synchronisation (après validation) : conflits={report2.result.conflicts} "
        f"en attente={report2.conflicts_pending_validation}"
    )


async def demo_signed_webhook_bridge() -> None:
    _print_section("3. Webhook entrant signé -> événement de workflow")

    get_event_bridge()  # s'assure que le pont vers workflow_automation est câblé

    workflow_bus = get_workflow_event_bus()
    received: list[IntegrationEventReceived] = []

    async def on_integration_event(event: IntegrationEventReceived) -> None:
        received.append(event)

    workflow_bus.subscribe(IntegrationEventReceived, on_integration_event)

    store = InMemoryWebhookSubscriptionStore()
    subscription = WebhookSubscription(
        id="wh-demo-1", connector_id="crm-demo", firm_id=FIRM_ID,
        url="https://cabinet.example/hook", direction=EventDirection.INBOUND, secret="secret-demo",
    )
    store.save(subscription)

    webhook_engine = WebhookEngine(store, LoggingWebhookSender(), get_integration_event_bus())

    payload = {"name": "Nouveau client détecté côté CRM"}
    body = json.dumps(
        {"entity_type": "client", "external_id": "cli-99", "payload": payload}, sort_keys=True
    ).encode()
    signature = sign_payload("secret-demo", body)

    ok = await webhook_engine.receive_inbound(
        subscription, body, signature, "client", "cli-99", payload
    )
    print(f"Livraison signée acceptée : {ok}")

    await asyncio.sleep(0)
    if received:
        event = received[0]
        print(
            f"Événement reçu côté workflow_automation : integration_name={event.integration_name} "
            f"label={event.label} payload={event.payload}"
        )


async def main() -> None:
    print(f"=== Démonstration Legal Integration Hub — {FIRM_NAME} ===")
    await demo_connectors_and_health()
    await demo_sync_with_mapping_and_conflict()
    await demo_signed_webhook_bridge()
    print(f"\nTerminé à {datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
