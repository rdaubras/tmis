# Guide — OAuth2 & OpenID Connect (Sprint 19)

## OAuth2 — Authorization Code grant

`identity_platform.oauth2.OAuth2Engine` implémente le grant
Authorization Code, pour la connexion interactive d'un utilisateur à
TMIS lui-même. Distinct de `cabinet_os.public_api.OAuthClient`
(Sprint 9, grant Client Credentials, accès machine-à-machine) — deux
grant types, deux usages, jamais confondus.

```python
from tmis.identity_platform.oauth2.engine import OAuth2Engine
from tmis.identity_platform.oauth2.store import (
    InMemoryAuthorizationCodeStore,
    InMemoryOAuth2ClientStore,
)

engine = OAuth2Engine(InMemoryOAuth2ClientStore(), InMemoryAuthorizationCodeStore())

# 1. Enregistrer un client (une fois, côté administration)
client, client_secret = engine.register_client(
    firm_id="firm-1", redirect_uris=("https://app.example.com/callback",)
)

# 2. Après authentification de l'utilisateur, émettre un code
code = engine.issue_authorization_code(
    client.client_id, user_id="user-1", firm_id="firm-1",
    redirect_uri="https://app.example.com/callback",
)

# 3. Le client échange le code contre des jetons
tokens = engine.exchange_code(
    client.client_id, client_secret, code, "https://app.example.com/callback"
)
# tokens.access_token, tokens.refresh_token
```

Le code d'autorisation est à usage unique (marqué `used=True` dès
l'échange) et expire après 5 minutes
(`oauth2.schemas.new_authorization_code_expiry`). Le secret client
n'est jamais stocké en clair : `_hash_client_secret` applique
SHA-256 + `hmac.compare_digest` (jamais bcrypt — un secret client est
un jeton opaque à haute entropie généré par le système, pas un mot de
passe choisi par un humain, même rationale que
`cabinet_os.public_api.security.hash_secret`).

## OpenID Connect

`identity_platform.openid_connect.OpenIdConnectEngine` compose
`oauth2.OAuth2Engine` directement et ajoute uniquement l'ID token —
jamais de réimplémentation du mécanisme Authorization Code.

```python
from tmis.identity_platform.openid_connect.engine import OpenIdConnectEngine

oidc = OpenIdConnectEngine(engine)  # engine = le OAuth2Engine ci-dessus

response = oidc.exchange_code(
    client.client_id, client_secret, code, "https://app.example.com/callback",
    email="user1@example.com", display_name="User One",
)
# response.access_token, response.refresh_token, response.id_token
```

`response.id_token` est un JWT distinct de `access_token`, réutilisant
`tmis.core.security.create_access_token` — il porte `firm_id`,
`email`, `name` en claims. Ce moteur comble le point d'extension
`platform.security.sso.OidcProviderPort` déclaré "architecture-only,
aucune implémentation ce sprint" au Sprint 10.

## Interfaces préparées pour SAML / IdP entreprise

`authentication.AuthStrategyPort` est un registre extensible : ajouter
un futur fournisseur SAML ou un autre IdP entreprise se fait en
enregistrant une nouvelle implémentation (`AuthenticationEngine.
register`), jamais en modifiant `AuthenticationEngine` lui-même. Aucun
fournisseur SAML n'est livré ce sprint — l'interface existe, pas
l'implémentation, même convention que `platform.security.sso.
SamlProviderPort` (Sprint 10).
