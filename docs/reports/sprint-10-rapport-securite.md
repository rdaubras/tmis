# Rapport de sécurité — Sprint 10 (Enterprise Platform)

## Mesures livrées

| Domaine | Mécanisme | Module |
|---|---|---|
| En-têtes HTTP | CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy | `security.headers` |
| CORS | Rejet explicite du joker `*` combiné à `allow_credentials=True` | `security.headers.validate_cors_origins` |
| CSRF | Double-submit-cookie, no-op sans cookie CSRF (défense en profondeur, auth principale par JWT) | `security.csrf` |
| Rate limiting | Fenêtre glissante configurable | `rate_limiting.limiter` |
| Protection brute force | Verrouillage après N échecs, réinitialisé par un succès | `rate_limiting.brute_force` |
| Rotation des secrets | Versions multiples, déchiffrement rétro-compatible (`MultiFernet`) | `security.secrets_rotation` |
| Chiffrement | Fernet (AES-128-CBC + HMAC), rejet explicite d'un texte chiffré altéré | `security.encryption` |
| Architecture SSO | Ports `OidcProviderPort`/`SamlProviderPort` (sans implémentation) | `security.sso` |
| Isolation multi-tenant | Vérification systématique (`require_same_firm`) + aide de test (`assert_tenant_isolated`) | `security.tenant_isolation` |
| Audit des permissions | Détection d'anomalie (rôle `CLIENT` avec override) | `audit.schemas.detect_anomaly` |

## Incident détecté et corrigé pendant le sprint

**Sévérité : élevée (corrigé avant livraison).** `CsrfProtect.verify()`
levait initialement une `fastapi.HTTPException` depuis un middleware
fonction (`@app.middleware("http")`). Une exception FastAPI levée à cet
endroit ne traverse pas la couche `ExceptionMiddleware` de Starlette et
remonterait comme une erreur 500 non gérée au lieu d'un 403 propre — un
attaquant présentant un cookie CSRF invalide aurait donc pu provoquer un
crash de la requête plutôt qu'un rejet contrôlé. Détecté en écrivant le
test d'intégration `test_csrf_middleware_blocks_a_mismatched_double_submit_cookie`
(`tests/integration/platform/test_platform_api_integration.py`). Corrigé
en faisant retourner un `bool` à `verify()` et en construisant
directement un `JSONResponse(status_code=403, ...)` dans
`csrf_middleware` — aucune exception ne traverse plus la pile de
middlewares. Couvert par 3 tests d'intégration dédiés.

## Scan de sécurité (CI)

- **Analyse statique (`bandit`)** : 0 problème de sévérité moyenne ou
  haute sur `src/` après correction d'un chemin `/tmp` en dur pour le
  stockage de sauvegarde local (`B108`, corrigé — la valeur par défaut
  utilise désormais un répertoire relatif au projet, configurable via
  `TMIS_BACKUP_STORAGE_DIR`).
- **Vulnérabilités de dépendances (`pip-audit`)** : 53 CVE relevées sur
  8 paquets — `ecdsa`, `langgraph`, `langgraph-checkpoint`,
  `langgraph-sdk`, `pillow`, `pypdf`, `pytest`, `starlette`. Toutes
  nécessitent une montée de version **majeure** de dépendances
  transitives critiques (notamment `starlette`, dont `fastapi` fixe la
  plage compatible) — hors périmètre de ce sprint ("aucune nouvelle
  fonctionnalité métier", contrainte de compatibilité stricte). Reporté
  au rapport de dette technique avec recommandation de sprint dédié.

## Ce qui reste hors périmètre (assumé)

- Aucun fournisseur SSO réel connecté (ports prêts, pas d'implémentation).
- Rotation de secrets en mémoire uniquement, pas de KMS réel branché.
- Aucun test de pénétration externe n'a été mené (le "pentest" reste
  prévu au Sprint 30 "Durcissement pré-lancement" de la roadmap).
