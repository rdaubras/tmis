# Guide — Créer un Nouveau Connecteur (SDK Développeur, Sprint 18)

## `BaseConnector` : le point de départ

`tmis.integration_hub.developer_sdk.base.BaseConnector` implémente
`ConnectorPort` avec des valeurs par défaut sûres, pour qu'un nouveau
connecteur n'ait besoin d'écrire que ce qu'il supporte réellement :

```python
from tmis.integration_hub.connector_framework import (
    ConnectorCapability, ConnectorRecord, ConnectorType, ConnectorWriteResult,
)
from tmis.integration_hub.developer_sdk import BaseConnector

class MyCrmConnector(BaseConnector):
    connector_type = ConnectorType.CRM
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        ...  # appelle le vrai système externe ici

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        ...
```

- `authenticate()` retourne `True` par défaut (beaucoup de systèmes
  utilisent une clé statique déjà résolue dans `config`) — à
  surcharger pour un vrai handshake OAuth2/OIDC.
- `read()`/`write()` lèvent `NotImplementedError` par défaut — un
  connecteur en lecture seule n'a jamais besoin d'écrire `write()`.

## Installer le connecteur : `register_connector`

```python
from tmis.integration_hub.developer_sdk import register_connector

descriptor = register_connector(
    registry, MyCrmConnector(),
    connector_id="mon-crm", name="Mon CRM", version="1.0.0", publisher="Éditeur X",
    permissions=("client:read", "client:write"),
    config_schema={"api_key": "string", "base_url": "string"},
)
```

`register_connector` construit le `ConnectorDescriptor` à partir des
`connector_type`/`capabilities` déclarés par l'implémentation et
l'enregistre en un seul appel dans le `ConnectorRegistryEngine`.

## Tester le connecteur : `testing`

`tmis.integration_hub.testing` fournit un harnais indépendant de tout
système externe réel :

- `InMemoryFakeConnector(records=[...], fail_auth=False)` — un
  `ConnectorPort` complet, en mémoire, pour vos propres tests
  (`written` capture ce qu'un job de synchronisation a poussé).
- `NoOpMetricsRecorder` — satisfait `ConnectorMetricsRecorderPort`
  sans rien enregistrer, pour des tests qui ne s'intéressent pas à la
  télémétrie.
- `assert_connector_conforms(connector, config)` — exerce
  `authenticate()`/`read()` (si `READ` est déclarée) et lève
  `ConnectorConformanceError` avec un message clair au premier écart
  de contrat, **avant** la mise en production du connecteur.

```python
from tmis.integration_hub.testing import assert_connector_conforms

async def test_my_connector_conforms():
    await assert_connector_conforms(MyCrmConnector(), {"api_key": "test"})
```

## Les 7 connecteurs de référence

`tmis.integration_hub.connectors` livre un connecteur de démonstration
par catégorie (`messaging`, `calendar`, `document_storage`,
`esignature`, `dms`, `billing`, `crm`) — chacun un `BaseConnector`
avec un jeu de données en mémoire, `READ`+`WRITE`, **sans logique
métier propre à un fournisseur**. Ils servent de squelette à copier :
un vrai connecteur Slack, Google Calendar ou DocuSign remplace
uniquement le corps de `read()`/`write()`/`authenticate()`, sans
toucher au reste du LIH (registre, synchronisation, webhooks...).

## Checklist avant mise en production

1. `capabilities` reflète exactement ce que `read()`/`write()`
   implémentent réellement.
2. `authenticate()` effectue un vrai handshake si le système cible
   l'exige.
3. `config_schema` documente tous les champs de configuration
   attendus.
4. `assert_connector_conforms()` passe en test.
5. Le connecteur est enregistré via `register_connector` dans
   `integration_hub/bootstrap.py` (ou l'équivalent du déploiement).
