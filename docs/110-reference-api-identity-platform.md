# Référence API — Enterprise Identity & Trust Platform (Sprint 19)

Base : `/api/v1/identity-platform`. Documentation interactive complète
sur `/docs` (OpenAPI, généré automatiquement par FastAPI).

## Organisations

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/organizations` | crée l'organisation d'un cabinet |
| `GET` | `/organizations/{firm_id}` | consulte l'organisation |

## Départements & équipes

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/departments` | crée un département |
| `GET` | `/departments` | `?firm_id=...` — départements du cabinet |
| `POST` | `/teams` | crée une équipe (rattachée à un département) |
| `GET` | `/teams` | `?firm_id=...&department_id=...` — équipes du département |

## Identité, rôles, permissions

| Méthode | Chemin | Rôle |
|---|---|---|
| `PUT` | `/identity-context` | fixe le profil métier d'un utilisateur |
| `GET` | `/identity-context` | `?firm_id=...&user_id=...` — profil (défaut si absent) |
| `POST` | `/roles` | assigne un rôle firm-wide |
| `GET` | `/roles` | `?firm_id=...&user_id=...` — rôles assignés |
| `GET` | `/permissions` | liste le vocabulaire de permissions |

## Politiques & autorisation

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/policies` | crée une politique configurable par cabinet |
| `GET` | `/policies` | `?firm_id=...` — politiques actives |
| `POST` | `/authorize` | évalue RBAC → ABAC → Policy (point d'entrée Zero Trust) |

## Sessions & appareils

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/sessions` | `?firm_id=...&user_id=...` — sessions d'un utilisateur |
| `POST` | `/sessions/{session_id}/revoke` | `?firm_id=...` — révoque une session |
| `POST` | `/devices` | enregistre un appareil (démarre `UNKNOWN`) |
| `GET` | `/devices` | `?firm_id=...&user_id=...` — appareils d'un utilisateur |
| `POST` | `/devices/{device_id}/trust` | `?firm_id=...` — marque `TRUSTED` |
| `POST` | `/devices/{device_id}/revoke` | `?firm_id=...` — marque `REVOKED` |

## Délégation

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/delegations` | crée une délégation temporaire de permissions |
| `GET` | `/delegations` | `?firm_id=...` — délégations actives du cabinet |
| `POST` | `/delegations/{delegation_id}/revoke` | `?firm_id=...` — révoque avant terme |

## Secrets

| Méthode | Chemin | Rôle |
|---|---|---|
| `PUT` | `/secrets` | chiffre et stocke un secret (jamais le clair en retour) |
| `GET` | `/secrets` | `?firm_id=...` — métadonnées des secrets (jamais le clair) |

## Sécurité & supervision

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/security-events` | `?firm_id=...` — historique du bus d'événements |
| `GET` | `/dashboard` | `?firm_id=...` — `IdentityDashboard` agrégé |

## Non exposés en API ce sprint

`authentication`/`oauth2`/`openid_connect`/`mfa`/`webauthn`/
`passkeys`/`passwordless`/`magic_links`/`impersonation`/`compliance`/
`configuration` sont livrés comme moteurs composables (voir
docs/104, 108) mais n'ont pas d'endpoint REST dédié ce sprint — ils
sont conçus pour être appelés par les points d'entrée
d'authentification propres à chaque canal client (web, mobile, API
publique), qui n'existent pas encore dans TMIS.
