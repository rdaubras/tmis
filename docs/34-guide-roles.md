# Guide — Rôles (RBAC)

## Les six rôles

`tmis.collaboration.roles.schemas.Role` :

| Rôle | Usage typique |
|---|---|
| `ADMINISTRATOR` | Gère l'espace de travail lui-même (paramètres, membres) |
| `ASSOCIATE` | Accès complet aux dossiers, documents, tâches, validations |
| `COLLABORATOR` | Contribue aux dossiers assignés, crée des tâches |
| `JURIST` | Rédige et commente, sans gérer l'équipe |
| `ASSISTANT` | Met à jour des tâches, commente, lecture des dossiers |
| `CLIENT` | Lecture limitée (dossiers et documents en lecture seule) |

## Affecter un rôle

Un membre détient **exactement un** rôle par espace de travail à la
fois — une nouvelle affectation remplace la précédente, elle ne
s'ajoute pas :

```python
from tmis.collaboration.roles.schemas import Role
from tmis.collaboration.roles.store import InMemoryRoleAssignmentStore

store = InMemoryRoleAssignmentStore()
store.assign(workspace_id, member_id, Role.ASSOCIATE)
store.get_role(workspace_id, member_id)  # Role.ASSOCIATE
```

Via l'API : `POST /api/v1/collaboration/workspaces/{id}/members/{id}/role`
avec `{"role": "associate", "actor_id": "..."}`.

## Rôles et permissions : deux modules séparés

`roles/` ne connaît pas les permissions — c'est
`permissions.ConfigurablePermissionEngine` qui traduit un rôle en
accès concret (voir docs/35-guide-permissions.md). Séparer les deux
permet de reconfigurer la matrice de permissions d'un rôle sans
toucher à l'affectation des rôles, et inversement.

## Retrouver qui détient un rôle

```python
store.list_by_role(workspace_id, Role.JURIST)  # -> list[member_id]
```

Utile pour cibler des notifications ou des approbateurs par défaut
(ex. « tous les Associés du dossier »).

## Ajouter un septième rôle

1. Ajouter la valeur à `Role` (`roles/schemas.py`).
2. Lui donner une entrée dans `_DEFAULT_MATRIX`
   (`permissions/engine.py`) — sinon il n'a aucune permission par
   défaut, ce qui est un choix valide (deny-by-default).
3. Aucun autre module n'a besoin de changer : `WorkspaceEngine`,
   l'API et les tests d'approbation raisonnent sur `Role` sans
   connaître la liste exhaustive des valeurs.
