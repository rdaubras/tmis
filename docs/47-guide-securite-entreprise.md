# Guide Sécurité Entreprise (Sprint 10)

## Périmètre

Ce guide couvre `tmis.platform.security`, `tmis.platform.rate_limiting`
et le durcissement multi-tenant. Il complète (sans le remplacer)
`docs/07-strategie-securite.md` (Sprint 1) qui pose les principes
généraux.

## En-têtes de sécurité

`SecurityHeadersMiddleware` (`platform/security/headers.py`) ajoute à
chaque réponse : `Content-Security-Policy` (politique restrictive
`default-src 'self'`), `Strict-Transport-Security` (HSTS, 2 ans,
uniquement sur HTTPS), `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`.

`validate_cors_origins()` refuse explicitement l'association `origin="*"`
+ `allow_credentials=True` — combinaison que le navigateur interdit mais
que FastAPI accepterait silencieusement sans ce garde-fou.

## CSRF

TMIS s'authentifie par jeton JWT porté en en-tête `Authorization` —
immunisé par nature contre le CSRF classique (le navigateur ne l'attache
jamais automatiquement). `CsrfProtect`/`csrf_middleware`
(double-submit-cookie) existent en **défense en profondeur** pour tout
endpoint ou intégration future s'appuyant sur un cookie : no-op tant
qu'aucun cookie `csrf_token` n'est présent.

**Point d'implémentation important** : `csrf_middleware` renvoie un
`JSONResponse(status_code=403, ...)` directement plutôt que de lever une
`HTTPException`. Une exception FastAPI levée depuis un middleware
fonction (`@app.middleware("http")`) ne traverse pas la couche
`ExceptionMiddleware` de Starlette et remonterait comme une erreur 500
non gérée — corrigé et couvert par
`tests/integration/platform/test_platform_api_integration.py`.

## Rate limiting & protection brute force

`InMemoryRateLimiter` (fenêtre glissante configurable) généralise
`tmis.cabinet_os.public_api.rate_limiter` (Sprint 9) sans le remplacer —
délibéré, pour ne prendre aucun risque de régression sur les tests déjà
verts du Sprint 9. `BruteForceProtector` verrouille une identité
(`ip:login`) après N échecs dans une fenêtre glissante ; un succès
réinitialise le compteur.

## Chiffrement

`FernetEncryption` (AES-128-CBC + HMAC via `cryptography`, déjà présent
transitivement via `python-jose[cryptography]`, maintenant dépendance
directe). `RotatingEncryption` + `SecretRotationPort` permettent de
faire tourner la clé sans casser le déchiffrement des données déjà
chiffrées (`MultiFernet`, clé la plus récente en écriture, toutes les
clés valides en lecture).

## SSO (architecture, pas d'implémentation)

`security/sso.py` définit `OidcProviderPort`/`SamlProviderPort` —
Protocols purs, sans implémentation. Objectif : qu'une intégration SSO
future (Sprint ultérieur) s'insère derrière un port déjà stable plutôt
que de redessiner l'authentification.

## Isolation multi-tenant

Voir `docs/46-architecture-enterprise.md` — section dédiée. En bref :
`require_same_firm` pour l'échec bruyant en production,
`assert_tenant_isolated` pour la détection en test.

## Ce qui reste à faire (voir rapport de dette technique)

- Rotation de secrets non branchée sur un vrai KMS (Vault, AWS Secrets
  Manager) — implémentation en mémoire uniquement.
- SSO : ports définis, aucun fournisseur réel connecté.
- Scan de vulnérabilités CI (`pip-audit`) remonte des CVE sur des
  dépendances transitives majeures (`pypdf`, `starlette`, `langgraph`) —
  correction reportée à un sprint dédié (bump de version majeure hors
  périmètre "aucune nouvelle fonctionnalité métier").
