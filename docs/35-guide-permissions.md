# Guide — Permissions

## La matrice par défaut

`tmis.collaboration.permissions.schemas.Permission` définit 17
permissions granulaires (`CASE_READ`, `CASE_WRITE`, `DOCUMENT_READ`,
`DOCUMENT_WRITE`, `DOCUMENT_DELETE`, `TASK_CREATE`, `TASK_ASSIGN`,
`TASK_UPDATE`, `COMMENT_WRITE`, `APPROVAL_REQUEST`,
`APPROVAL_DECIDE`, `SHARING_CREATE_LINK`, `SHARING_REVOKE_LINK`,
`MEMBER_INVITE`, `MEMBER_MANAGE`, `ROLE_ASSIGN`,
`WORKSPACE_MANAGE`). `permissions/engine.py` associe chaque `Role` à un
sous-ensemble par défaut (`_DEFAULT_MATRIX`) — `ADMINISTRATOR` les a
toutes, `CLIENT` n'a que la lecture.

## Vérifier une permission

```python
from tmis.collaboration.permissions.engine import ConfigurablePermissionEngine
from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.schemas import Role

engine = ConfigurablePermissionEngine()
engine.has_permission(workspace_id, member_id, Role.COLLABORATOR, Permission.TASK_CREATE)
```

`WorkspaceEngine.has_permission(workspace_id, member_id, permission)`
fait le travail complet : récupérer le rôle du membre puis appeler
`has_permission` — c'est la méthode à utiliser depuis l'API ou un
appelant qui ne connaît pas déjà le rôle.

## Dérogations par membre : grant / revoke

Un octroi ou une révocation s'ajoute par-dessus la matrice, sans la
modifier :

```python
engine.grant_override(workspace_id, member_id, Permission.TASK_CREATE)
engine.revoke_override(workspace_id, member_id, Permission.CASE_WRITE)
```

**Précédence (deny-overrides) : une révocation l'emporte toujours**,
même sur un octroi explicite. Un administrateur peut donc verrouiller
un membre précis sans toucher au rôle partagé par toute l'équipe, et
sans qu'un octroi ultérieur mal placé ne rouvre l'accès par erreur.
Octroyer *après* avoir révoqué efface bien la révocation ; c'est
l'ordre des appels qui compte, pas leur nombre.

## Reconfigurer un rôle entier

```python
engine.set_role_permissions(Role.CLIENT, {Permission.CASE_READ, Permission.COMMENT_WRITE})
```

Remplace tout le jeu de permissions du rôle pour cette instance de
moteur — utile pour un cabinet qui veut, par exemple, autoriser ses
clients à commenter.

## Portée des dérogations

Chaque dérogation est scopée par `(workspace_id, member_id)` : révoquer
une permission à un membre dans un espace de travail ne l'affecte ni
dans un autre espace, ni pour un autre membre du même espace.
