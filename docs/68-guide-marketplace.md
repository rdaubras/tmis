# Guide de la Marketplace (Sprint 13)

## Rôle

`tmis.platform_sdk.marketplace` est le catalogue de découverte des
plugins **publiés** — recherche, catégories, avis — au-dessus du
registre global (`tmis.platform_sdk.plugin_registry`) et du cycle de
vie d'installation par cabinet
(`tmis.platform_sdk.extensions.ExtensionEngine`). Conformément à
l'énoncé du sprint, aucune interface utilisateur complète n'est
livrée — uniquement le backend et l'API REST.

## Ce qui est visible dans la Marketplace

Uniquement les manifestes au statut `PUBLISHED` (voir
docs/69-guide-plugins.md pour le cycle de vie complet) — un plugin en
développement, validé ou signé n'apparaît jamais dans une recherche.

```python
marketplace = get_marketplace_engine()
marketplace.search(query="fiscal", plugin_type=PluginType.AGENT)
marketplace.categories()  # types de plugins publiés
```

## Avis

```python
marketplace.submit_review("agent-fiscal", firm_id="firm-demo", rating=5, comment="Très utile")
marketplace.average_rating("agent-fiscal")  # 0.0 si aucun avis
marketplace.reviews_for("agent-fiscal")
```

Une note hors de `[1, 5]` lève `InvalidRatingError`.

## Installation, mise à jour, désinstallation

Ces trois opérations sont de simples délégations vers
`tmis.platform_sdk.extensions.ExtensionEngine` — la Marketplace ne
duplique pas cette logique, elle y ajoute la découverte :

```python
marketplace.install(firm_id, "agent-fiscal", frozenset({ExtensionPermission.ACCESS_KNOWLEDGE}))
marketplace.update(firm_id, "agent-fiscal")
marketplace.uninstall(firm_id, "agent-fiscal")
marketplace.install_count("agent-fiscal")  # nombre de cabinets l'ayant installé
```

`install()` refuse un plugin non publié
(`PluginNotAvailableError`) et refuse toute permission demandée qui ne
serait pas déclarée dans le manifeste (`UngrantablePermissionError`) —
voir docs/69-guide-plugins.md.

## API

| Endpoint | Rôle |
|---|---|
| `GET /platform-sdk/marketplace` | recherche (`query`, `plugin_type`) |
| `GET /platform-sdk/marketplace/categories` | catégories publiées |
| `POST /platform-sdk/marketplace/{id}/install` | installer pour un cabinet |
| `POST /platform-sdk/marketplace/{id}/update` | mettre à jour |
| `POST /platform-sdk/marketplace/{id}/uninstall` | désinstaller |
| `POST /platform-sdk/marketplace/{id}/reviews` | soumettre un avis |
| `GET /platform-sdk/marketplace/{id}/reviews` | lister les avis |
| `GET /platform-sdk/extensions` | extensions installées d'un cabinet |
