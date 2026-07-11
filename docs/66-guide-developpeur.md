# Guide développeur TMIS (Sprint 13)

## Démarrer

Le SDK officiel de TMIS vit sous `tmis.platform_sdk`. Un plugin est
toujours composé de deux choses :

1. un **manifeste** (`tmis.platform_sdk.plugin_system.schemas.
   PluginManifest`) — son identité déclarative (id, version, auteur,
   permissions, dépendances, licence, description, compatibilité) ;
2. une **implémentation** — une classe qui satisfait
   `tmis.platform_sdk.sdk.ports.PluginPort`, en pratique en héritant
   d'une des classes de base fournies par un `*_sdk`
   (`agent_sdk.BaseAgentPlugin`, `connector_sdk.BaseConnectorPlugin`,
   `document_sdk.BaseDocumentTemplatePlugin`) ou en assemblant un
   `workflow_sdk.WorkflowDefinition` (déclaratif, pas de classe).

## Tutoriel

### 1. Scaffolder le plugin

```bash
cd backend
python -m tmis.platform_sdk.cli create-plugin \
    --id mon-agent --type agent --author "Mon Cabinet" --output ./plugins
```

Cela crée `plugins/mon-agent/manifest.json` et `plugins/mon-agent/plugin.py`
(un stub prêt à compléter, héritant de `BaseAgentPlugin`).

### 2. Implémenter

Complétez `plugin.py` — pour un agent, override `capabilities` et
`run()` (voir docs/67-guide-sdk.md et docs/71-guide-connecteurs.md
pour les autres types).

### 3. Valider

```bash
python -m tmis.platform_sdk.cli validate-plugin --manifest plugins/mon-agent/manifest.json
```

Contrôle la conformité, les permissions déclarées, la compatibilité et
les dépendances (voir docs/69-guide-plugins.md).

### 4. Empaqueter

```bash
python -m tmis.platform_sdk.cli package-plugin --path plugins/mon-agent --output ./dist
```

### 5. Publier puis installer

```bash
python -m tmis.platform_sdk.cli publish-plugin --id mon-agent
python -m tmis.platform_sdk.cli install-plugin --firm-id firm-demo --id mon-agent --permissions read_cases
```

`publish-plugin` fait avancer le manifeste jusqu'à `published` en
appliquant chaque étape restante (validation → signature →
publication) — voir docs/69-guide-plugins.md pour le détail du cycle
de vie et pourquoi ces étapes ne peuvent pas être sautées.

## Contraintes à respecter

- **Jamais d'accès direct** à un fournisseur de modèle, un
  connecteur, ou tout module métier interne : tout passe par les
  ports exposés dans `PluginContext` (`context.kernel`,
  `context.events`, `context.permissions`).
- **Ne déclarer que les permissions réellement utilisées** — voir
  docs/69-guide-plugins.md#bonnes-pratiques.
- **Aucun code arbitraire** : un workflow est toujours de la donnée
  (voir docs/70-guide-workflows.md), jamais une chaîne évaluée.

## Voir aussi

- docs/67-guide-sdk.md — le contrat commun (`PluginContext`/`PluginPort`)
- docs/68-guide-marketplace.md — publier et découvrir des plugins
- docs/69-guide-plugins.md — manifeste, permissions, sandbox, cycle de vie
- docs/70-guide-workflows.md — workflows déclaratifs
- docs/71-guide-connecteurs.md — le SDK connecteur
- docs/72-reference-api-platform-sdk.md — référence API REST
- `backend/src/tmis/platform_sdk/examples/` — cinq plugins complets
