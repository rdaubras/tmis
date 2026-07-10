# Guide — API publique

## API Keys

```python
from tmis.cabinet_os.public_api.engine import PublicApiEngine
from tmis.cabinet_os.public_api.schemas import ApiScope

key, raw_key = public_api.issue_api_key(
    "firm-1", "Intégration CRM externe", frozenset({ApiScope.READ_CLIENTS}),
)
# raw_key n'est renvoyé qu'une seule fois, à l'émission — seul son hash
# SHA-256 (key.key_hash) est conservé.
```

```python
authenticated = public_api.authenticate_api_key(raw_key)  # None si révoquée/invalide
public_api.revoke_api_key(key.id)
```

`key.prefix` (les 8 premiers caractères du secret) permet d'afficher la
clé dans une liste sans jamais en révéler le secret complet une
seconde fois.

## OAuth2 — flux client-credentials

```python
client, raw_secret = public_api.register_oauth_client(
    "firm-1", ["https://client.example/callback"], frozenset({ApiScope.READ_BILLING}),
)
token = public_api.issue_oauth_token(client.client_id, raw_secret)
public_api.authenticate_oauth_token(token.token)
```

**Limite connue** : seul le grant client-credentials (accès
machine-à-machine) est couvert ce sprint. Un flux délégué par
l'utilisateur (authorization code, avec écran de consentement) reste à
construire pour une intégration tierce agissant au nom d'un avocat.

## Scopes

`ApiScope` est volontairement grossier (`read:clients`,
`write:billing`, `admin`...) plutôt qu'une permission par endpoint —
voir `tmis.collaboration.permissions` (Sprint 8) pour un modèle plus
fin si un scope public doit un jour être aussi granulaire que le RBAC
interne. `ApiScope.ADMIN` implique automatiquement tous les autres
scopes (`PublicApiEngine.has_scope`).

## Rate limiting

```python
from tmis.cabinet_os.public_api.rate_limiter import InMemoryRateLimiter
from tmis.cabinet_os.public_api.schemas import RateLimitPolicy

limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_minute=60, burst=10))
result = limiter.check(api_key.id)
# result.allowed, result.remaining, result.retry_after_seconds
```

Fenêtre fixe d'une minute, en mémoire — une vraie mise en production
échangerait `InMemoryRateLimiter` contre un limiteur distribué (ex.
seau à jetons Redis) derrière le même `RateLimiterPort`, sans changer
`PublicApiEngine`.

## Versionnage

Le versionnage est un choix de routage, pas un comportement du moteur :
chaque version est montée sous son propre préfixe
(`/api/v1/public-api/v1/...`) ; une v2 se monterait à côté, sans
dupliquer `PublicApiEngine`.

## Documentation OpenAPI

Toutes les routes sont documentées automatiquement via `/docs` et
`/openapi.json`, comme le reste de l'API TMIS.
