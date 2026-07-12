"""Standalone event hierarchy for the Enterprise Identity & Trust
Platform.

Deliberately its own hierarchy — mirrors
`tmis.collaboration.event_bus.CollaborationEvent`,
`tmis.workflow_automation.event_bus.WorkflowEvent` and
`tmis.integration_hub.event_bridge.IntegrationEvent` — rather than
sharing any of them. The sprint's own examples: "Connexion,
Déconnexion, Échec MFA, Changement de rôle, Création d'une
délégation, Nouvel appareil, Révocation de session".
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True)
class SecurityEvent:
    firm_id: str
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        return type(self).__name__


@dataclass(frozen=True, kw_only=True)
class LoginSucceeded(SecurityEvent):
    user_id: str
    method: str


@dataclass(frozen=True, kw_only=True)
class LoginFailed(SecurityEvent):
    identity: str
    reason: str


@dataclass(frozen=True, kw_only=True)
class LogoutOccurred(SecurityEvent):
    user_id: str


@dataclass(frozen=True, kw_only=True)
class MfaChallengeFailed(SecurityEvent):
    user_id: str


@dataclass(frozen=True, kw_only=True)
class RoleChanged(SecurityEvent):
    user_id: str
    role: str
    action: str


@dataclass(frozen=True, kw_only=True)
class DelegationCreated(SecurityEvent):
    delegator_id: str
    delegate_id: str


@dataclass(frozen=True, kw_only=True)
class NewDeviceDetected(SecurityEvent):
    user_id: str
    device_id: str


@dataclass(frozen=True, kw_only=True)
class SessionRevoked(SecurityEvent):
    user_id: str
    session_id: str
