from tmis.platform_sdk.bootstrap import (
    get_extension_engine,
    get_marketplace_engine,
    get_plugin_registry,
    get_publishing_engine,
    get_sandbox_executor,
)
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.plugin_system.schemas import PublishingStatus


def _publish_all() -> None:
    registry = get_plugin_registry()
    publishing = get_publishing_engine()
    for manifest in registry.list_all():
        if manifest.status is PublishingStatus.DEVELOPMENT:
            publishing.validate_manifest(manifest.id, actor="dev1")
        if manifest.status is PublishingStatus.VALIDATED:
            publishing.sign_manifest(manifest.id, actor="dev1")
        if manifest.status is PublishingStatus.SIGNED:
            publishing.publish(manifest.id, actor="dev1")


def test_example_plugins_are_registered_at_bootstrap() -> None:
    registry = get_plugin_registry()

    ids = {m.id for m in registry.list_all()}

    assert ids >= {
        "agent-fiscal",
        "agent-droit-social",
        "connector-ged",
        "workflow-validation",
        "document-template-consultation",
    }


def test_publishing_pipeline_reaches_published_for_every_example() -> None:
    _publish_all()
    registry = get_plugin_registry()

    assert all(m.status is PublishingStatus.PUBLISHED for m in registry.list_all())
    assert all(m.signature is not None for m in registry.list_all())


async def test_sandbox_executes_agent_fiscal_end_to_end() -> None:
    _publish_all()
    firm_id = "firm-integration-1"
    extensions = get_extension_engine()
    extensions.install(
        firm_id,
        "agent-fiscal",
        frozenset({ExtensionPermission.ACCESS_KNOWLEDGE, ExtensionPermission.ACCESS_RESEARCH}),
    )
    sandbox = get_sandbox_executor()

    result = await sandbox.execute(
        firm_id,
        "avocat1",
        "agent-fiscal",
        {"context": {"question": "TVA applicable sur une prestation de conseil ?"}},
        ExtensionPermission.ACCESS_KNOWLEDGE,
    )

    assert result.success is True
    assert result.result is not None
    assert "text" in result.result["result"]


async def test_sandbox_denies_agent_without_grant() -> None:
    _publish_all()
    firm_id = "firm-integration-2"
    sandbox = get_sandbox_executor()

    result = await sandbox.execute(
        firm_id, "avocat1", "agent-fiscal", {}, ExtensionPermission.ACCESS_KNOWLEDGE
    )

    assert result.success is False
    assert result.error == "permission refusée"


async def test_sandbox_executes_workflow_validation_with_no_required_permission() -> None:
    """`workflow-validation` legitimately declares zero permissions —
    it must still be executable by passing `required_permission=None`
    (see `SandboxExecutor.execute`)."""
    _publish_all()
    firm_id = "firm-integration-3"
    extensions = get_extension_engine()
    extensions.install(firm_id, "workflow-validation", frozenset())
    sandbox = get_sandbox_executor()

    low_amount = await sandbox.execute(
        firm_id, "avocat1", "workflow-validation", {"amount": 500}
    )

    assert low_amount.success is True
    assert low_amount.result is not None
    assert low_amount.result["executed_step_ids"] == ["check-amount", "auto-approve"]


async def test_sandbox_executes_connector_ged() -> None:
    _publish_all()
    firm_id = "firm-integration-4"
    extensions = get_extension_engine()
    extensions.install(firm_id, "connector-ged", frozenset({ExtensionPermission.READ_DOCUMENTS}))
    sandbox = get_sandbox_executor()

    result = await sandbox.execute(
        firm_id,
        "avocat1",
        "connector-ged",
        {"query": "contrat"},
        ExtensionPermission.READ_DOCUMENTS,
    )

    assert result.success is True
    assert result.result is not None
    assert len(result.result["items"]) >= 1


def test_marketplace_reflects_published_examples_with_reviews() -> None:
    _publish_all()
    marketplace = get_marketplace_engine()
    marketplace.submit_review("agent-fiscal", "firm-a", 5, "Excellent")

    listings = marketplace.search()

    assert "agent-fiscal" in [m.id for m in listings]
    assert marketplace.average_rating("agent-fiscal") == 5.0


def test_uninstalling_revokes_sandbox_access() -> None:
    _publish_all()
    firm_id = "firm-integration-5"
    extensions = get_extension_engine()
    extensions.install(firm_id, "agent-fiscal", frozenset({ExtensionPermission.ACCESS_KNOWLEDGE}))

    extensions.uninstall(firm_id, "agent-fiscal")

    from tmis.platform_sdk.bootstrap import get_permission_engine

    assert (
        get_permission_engine().check(firm_id, "agent-fiscal", ExtensionPermission.ACCESS_KNOWLEDGE)
        is False
    )
