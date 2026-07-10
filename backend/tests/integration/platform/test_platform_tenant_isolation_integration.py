from tmis.cabinet_os.clients.schemas import ClientType
from tmis.cabinet_os.clients.service import ClientService
from tmis.cabinet_os.clients.store import InMemoryClientStore
from tmis.collaboration.workspace.schemas import Workspace
from tmis.collaboration.workspace.store import InMemoryWorkspaceStore
from tmis.platform.security.tenant_isolation import assert_tenant_isolated


def test_client_store_list_for_firm_never_leaks_another_firms_clients() -> None:
    """The "tests d'étanchéité" the sprint requires (see
    docs/47-guide-securite-entreprise.md — Multi-tenant hardening):
    every `list_for_firm`-style query across a business module must be
    exercised against `assert_tenant_isolated` to catch a leaking store
    before it ever reaches an API response."""
    store = InMemoryClientStore()
    service = ClientService(store)
    service.create("firm-1", ClientType.INDIVIDUAL, "Client A")
    service.create("firm-1", ClientType.INDIVIDUAL, "Client B")
    service.create("firm-2", ClientType.ORGANIZATION, "Client C")

    firm_1_clients = store.list_for_firm("firm-1")

    assert len(firm_1_clients) == 2
    assert_tenant_isolated(firm_1_clients, lambda c: c.firm_id, "firm-1")


def test_workspace_store_list_for_firm_never_leaks_another_firms_workspaces() -> None:
    store = InMemoryWorkspaceStore()
    store.save(Workspace(id="ws-1", firm_id="firm-1", name="Workspace 1"))
    store.save(Workspace(id="ws-2", firm_id="firm-1", name="Workspace 2"))
    store.save(Workspace(id="ws-3", firm_id="firm-2", name="Other firm's workspace"))

    firm_1_workspaces = store.list_for_firm("firm-1")

    assert len(firm_1_workspaces) == 2
    assert_tenant_isolated(firm_1_workspaces, lambda w: w.firm_id, "firm-1")


def test_assert_tenant_isolated_catches_a_deliberately_broken_query() -> None:
    """Negative control: proves the helper actually fails when a query
    is broken, rather than trivially passing on any input."""
    service = ClientService(InMemoryClientStore())
    firm_1_client = service.create("firm-1", ClientType.INDIVIDUAL, "Client A")
    firm_2_client = service.create("firm-2", ClientType.INDIVIDUAL, "Client B")

    unscoped_results = [firm_1_client, firm_2_client]

    try:
        assert_tenant_isolated(unscoped_results, lambda c: c.firm_id, "firm-1")
        raised = False
    except AssertionError:
        raised = True

    assert raised is True
