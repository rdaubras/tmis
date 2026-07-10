from typing import Protocol

from tmis.cabinet_os.dashboard.schemas import (
    AdminDashboard,
    CabinetDashboard,
    CollaboratorDashboard,
)


class DashboardEnginePort(Protocol):
    """Port implemented by every interchangeable dashboard engine."""

    def cabinet_dashboard(self, firm_id: str) -> CabinetDashboard: ...

    def collaborator_dashboard(
        self, firm_id: str, collaborator_id: str
    ) -> CollaboratorDashboard: ...

    def admin_dashboard(self, firm_id: str) -> AdminDashboard: ...
