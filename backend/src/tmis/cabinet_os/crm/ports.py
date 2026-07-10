from typing import Protocol

from tmis.cabinet_os.clients.schemas import Client
from tmis.cabinet_os.crm.schemas import ClientProfile


class CRMEnginePort(Protocol):
    """Port implemented by every interchangeable CRM engine."""

    def get_profile(self, client_id: str) -> ClientProfile: ...

    def search(self, firm_id: str, query: str) -> list[Client]: ...
