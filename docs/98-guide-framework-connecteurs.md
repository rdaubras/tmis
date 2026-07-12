# Guide — Framework de Connecteurs (Sprint 18)

## `ConnectorPort` : le contrat commun

Tout connecteur du Legal Integration Hub implémente
`tmis.integration_hub.connector_framework.ports.ConnectorPort` :

```python
class ConnectorPort(Protocol):
    connector_type: ConnectorType
    capabilities: frozenset[ConnectorCapability]

    async def authenticate(self, config: dict[str, str]) -> bool: ...
    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]: ...
    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult: ...
```

`capabilities` déclare ce que le connecteur supporte réellement
(`READ`, `WRITE`, `SYNC`) ; un connecteur en lecture seule (ex.
`ESIGNATURE` côté statut de signature) déclare `{READ}` uniquement.

## `ConnectorInvoker` : toujours journalisé, jamais silencieux

`connector_framework.engine.ConnectorInvoker` enveloppe chaque appel :

- `safe_read` : chronomètre l'appel, enregistre un événement de
  métrique de succès ou d'échec via `ConnectorMetricsRecorderPort`,
  puis **relance l'exception** en cas d'échec (il n'existe pas de
  forme partielle raisonnable pour une lecture ratée).
- `safe_write` : même chronométrage/journalisation, mais **ne relance
  jamais** — en cas d'exception, retourne
  `ConnectorWriteResult(success=False, detail=...)`, pour qu'un job de
  synchronisation puisse continuer sur les autres enregistrements.

`ConnectorMetricsRecorderPort` est une entrée découplée : `monitoring.
ConnectorMonitoringEngine` la satisfait structurellement sans que
`connector_framework` importe `monitoring`.

## `connector_registry` : installation dynamique

```python
registry = ConnectorRegistryEngine(InMemoryConnectorRegistryStore())
registry.register(descriptor, implementation)   # installation
registry.disable("crm-demo")                    # désactivation
registry.enable("crm-demo")
registry.list_connectors(connector_type=ConnectorType.CRM, status=ConnectorStatus.ACTIVE)
```

Le `ConnectorDescriptor` (nom, version, éditeur, capacités,
permissions, `config_schema`) est stocké séparément de
l'implémentation — l'un peut être listé pour l'UI sans exposer
l'objet Python.

## `authentication` : une stratégie par méthode

`AuthenticationEngine` dispatch vers une `AuthStrategyPort` selon
`AuthMethod` (OAuth2, OIDC, clé d'API, JWT, certificat) — chacune ne
fait que vérifier la présence des champs requis dans
`AuthCredentials.values`. Ajouter une méthode d'authentification ne
touche jamais le moteur : `engine.register(NouvelleStrategie())`.

## `security` : chiffrement, rotation, isolation tenant

`IntegrationSecurityEngine` compose directement
`platform.security.encryption`, `platform.security.secrets_rotation`
et `platform.security.tenant_isolation` (Sprint 10) :

```python
engine.encrypt_config({"token": "secret"})   # base64(chiffré)
engine.decrypt_config(encrypted)
engine.check_rate_limit("connector-1")       # platform.rate_limiting
engine.require_tenant(context, resource_firm_id)  # lève TenantAccessError si différent
```

## `sandbox` : quota + timeout

`ConnectorSandbox.run(firm_id, connector_id, operation)` applique un
quota d'appels glissant (60/minute par défaut) et un timeout dur (10 s
par défaut) autour de n'importe quel appel asynchrone, et retourne
toujours un `SandboxExecutionResult` (jamais d'exception non
capturée).

## `configuration` : validée par schéma

`ConfigurationEngine.set_configuration(connector_id, firm_id, values,
descriptor)` vérifie que tous les champs de
`descriptor.config_schema` sont présents avant d'enregistrer —
`ConfigurationValidationError` sinon.

## `health` et `monitoring`

`health.register_connector_health_checks(engine, registry)` enregistre
un `CallableHealthCheck` par connecteur (sain tant que son descripteur
est `ACTIVE`) sur un `platform.health.HealthCheckEngine`.
`monitoring.ConnectorMonitoringEngine` fait suivre chaque lecture/
écriture à une liste de sinks (`InMemoryConnectorMetricsSink` par
défaut), avec `success_rate(connector_id)` pour un tableau de bord.

Voir `docs/99-guide-creation-connecteur.md` pour construire un nouveau
connecteur à partir de ce framework.
