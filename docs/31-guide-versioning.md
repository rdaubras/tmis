# Guide : le système de versioning du Legal Drafting Studio

`versioning.InMemoryVersioningService` prend un instantané
(`DocumentVersion`) à chaque étape qui modifie le contenu d'un
brouillon : création, régénération de section, régénération de
paragraphe, restauration. Chaque instantané est une **copie profonde**
des sections (`dataclasses.replace` récursif sur sections et
paragraphes) — modifier le document en mémoire après coup ne change
jamais une version déjà enregistrée.

## Numérotation

Les numéros de version démarrent à 1 et s'incrémentent strictement pour
un `document_id` donné (`len(existing) + 1`) — jamais de trou, jamais de
réutilisation.

## Comparer deux versions

```python
diff = versioning_service.compare(document_id, version_a=1, version_b=2)
# VersionDiff(
#     version_a=1, version_b=2,
#     added_paragraph_ids=(...),    # présents en v2, absents en v1
#     removed_paragraph_ids=(...),  # présents en v1, absents en v2
#     changed_paragraph_ids=(...),  # même id, texte différent
# )
```

La comparaison se fait à la granularité du paragraphe, par id — c'est
pourquoi `DocumentOrchestrator.regenerate_section()` réaligne
volontairement les ids des paragraphes régénérés sur ceux de la section
précédente (voir docs/28-legal-drafting.md — Document Builder) : sans
cela, régénérer une section apparaîtrait toujours comme "tout supprimé,
tout ajouté" plutôt que "modifié", ce qui rendrait la comparaison
inutilisable pour l'avocat qui veut voir ce qui a réellement changé.

## Restaurer une version

```python
sections = versioning_service.restore(document_id, version_number=1)
document.sections = sections
```

`restore()` renvoie une copie des sections de la version demandée —
jamais une référence partagée avec l'instantané stocké. L'orchestrateur
prend ensuite un nouvel instantané après restauration
(`VERSION_RESTORED` dans l'historique), pour que la restauration
elle-même reste traçable : restaurer la version 1 alors qu'on est en
version 3 crée une version 4 identique à la version 1, elle ne
supprime jamais les versions 2 et 3.

## API

| Route | Rôle |
|---|---|
| `GET /legal-drafting/drafts/{id}/versions` | Liste toutes les versions |
| `GET /legal-drafting/drafts/{id}/versions/compare?version_a=&version_b=` | Diff à la granularité du paragraphe |
| `POST /legal-drafting/drafts/{id}/versions/{n}/restore` | Restaure (en créant une nouvelle version) |
