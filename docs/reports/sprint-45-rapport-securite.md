# Rapport de fin de sprint — Sprint sécurité (Authentification & Isolation multi-tenant)

## Résumé exécutif

Avant ce sprint, l'API n'avait **aucune frontière d'authentification
réelle** : `0` route sur ~420 dépendait d'une vérification d'identité, et
le tenant (`firm_id`) provenait d'un header `X-Firm-Id` fourni par le
client — falsifiable par construction (IDOR). `tmis.identity_platform`
émettait des JWT (OAuth2, magic links, OIDC) que personne ne validait
côté requête.

Ce sprint rend l'authentification et l'isolation multi-tenant **default-
deny et par défaut**, pas optionnelles :

- `POST /auth/login` (email + mot de passe) et `POST /auth/refresh` sont
  les deux seules routes qui émettent des tokens.
- Toute route sous `/api/v1`, hors une allowlist explicite (`/health`,
  `/auth/login`, `/auth/refresh`), exige désormais
  `Authorization: Bearer <access_token>` — appliqué au niveau du routeur
  agrégateur, pas route par route.
- Le tenant (`firm_id`) vient exclusivement du token validé ; le header
  `X-Firm-Id` n'a plus aucun effet nulle part dans le code.
- Un secret JWT manquant ou faible (< 32 caractères) fait échouer le
  démarrage de l'application hors mode debug (fail-fast).
- Une suite `tests/security/` (72 tests) démontre chacune de ces
  propriétés — non authentifié → 401, cross-tenant → 404, token altéré/
  `alg=none`/expiré/mauvais type → 401, mauvais rôle → 403, énumération
  de comptes impossible au login.

**Résultat** : 2 329 tests passent (0 échec), couverture globale 96 %
(seuil CI : 90 %), `bandit -ll` : aucun problème, aucune route protégée
ne répond plus sans jeton valide.

## Décisions d'architecture

- **ADR-SEC-01** : `tmis.domain.identity` + un nouveau
  `SqlAlchemyUserRepository` (persistant) est l'unique source
  d'authentification pour ce sprint. `tmis.identity_platform` (RBAC/OIDC/
  MFA riches, mais en mémoire) reste une IAM non branchée sur le chemin
  de requête réel — dette assumée, voir plus bas.
- **ADR-SEC-02** : `tmis.api.v1.router.protected_router` porte
  `dependencies=[Depends(get_current_principal)]` ; `public_router` porte
  l'allowlist. Un nouveau module métier ajouté à `protected_router` est
  protégé sans action supplémentaire de son auteur.

## Composants créés

- `tmis.core.security` (durci) : allowlist d'algorithmes fixée par la
  configuration serveur (jamais dérivée du header du token — bloque
  `alg=none` et la confusion d'algorithme), claims `iss`/`aud`/`jti`
  ajoutés et vérifiés au décodage, `create_access_token` (15 min) et
  `create_refresh_token` (7 j) distincts via un claim `token_type`
  vérifié dans les deux sens.
- `tmis.api.deps` : `Principal` (dataclass gelée), `get_current_principal`
  (`HTTPBearer` → décode → 401 générique sur tout échec, jamais 500),
  `get_current_firm_id`, `require_role`, `require_scope`.
- `tmis.api.v1.auth` (`schemas.py`, `routes.py`) : `POST /auth/login`,
  `POST /auth/refresh`.
- `tmis.application.identity.commands` : `LoginUseCase`/`RefreshUseCase` —
  hash factice comparé même pour un email inconnu (résistance timing),
  réponse 401 identique pour email inconnu / mauvais mot de passe /
  compte inactif, rotation du refresh (utilisateur rechargé depuis le
  repository, jamais depuis les anciens claims).
- `tmis.core.tenancy.scoped_query` : garde-fou d'isolation — refuse
  (`TypeError`) de construire une requête sur un modèle sans colonne
  `firm_id`, plutôt que de compter sur la convention.
- `tmis.infrastructure.persistence.repositories.SqlAlchemyUserRepository` :
  implémente `UserRepositoryPort` (jusqu'ici sans aucune implémentation).
- `tests/security/` : 5 fichiers, 72 tests (accès non authentifié,
  isolation tenant, validation de token, RBAC, login).

## Composants modifiés

- `tmis.core.config.Settings` : `jwt_secret_key` perd sa valeur par
  défaut `"change-me-in-production"` ; un `model_validator` fait échouer
  le démarrage si le secret fait moins de 32 caractères hors
  `TMIS_DEBUG=true`. `access_token_expire_minutes` passe de 30 à 15 ;
  nouveaux `jwt_issuer`/`jwt_audience`/`refresh_token_expire_days`.
- `tmis.domain.identity.ports.UserRepositoryPort.get_by_email` perd son
  paramètre `firm_id` (email globalement unique — voir `UserModel.email,
  unique=True` — et le login n'a justement pas de tenant fourni par le
  client à ce stade).
- `tmis.api.v1.case.routes` : suppression complète de
  `get_current_firm_id(x_firm_id: Header(...))` ; ajout de
  `GET /cases/{case_id}` (manquait pour pouvoir tester l'isolation
  cross-tenant en lecture directe).
- `tmis.api.v1.router` : scindé en `public_router`/`protected_router`
  (voir ADR-SEC-02).
- `tmis.identity_platform.api.routes` : `GET /dashboard` et
  `GET /security-events` gagnent `Depends(require_role("firm_admin",
  "platform_admin"))` — pattern RBAC posé, pas généralisé.
- `tmis.infrastructure.persistence.repositories.SqlAlchemyCaseRepository` :
  requêtes reconstruites sur `scoped_query`.

## Composants réutilisés

- `passlib`/`python-jose` (déjà en dépendance) pour le hash de mot de
  passe et le JWT — aucune nouvelle dépendance de sécurité ajoutée.
- Le modèle de test `TestClient` + sqlite éphémère déjà en place dans
  `tests/integration/case_intelligence/test_case_api.py`, repris pour
  `tests/security/conftest.py`.

## Correction annexe (bloquante, hors périmètre initial)

`passlib` 1.7.4 (non maintenu en amont) sonde `bcrypt` avec un test de
compatibilité interne au chargement, et casse sur `bcrypt>=4.1` (limite
des 72 octets resserrée). Comme **aucun code existant n'appelait
`hash_password`/`verify_password` avant ce sprint** (il n'y avait pas de
flux de login), ce bug latent n'avait jamais été déclenché. `bcrypt` est
désormais épinglé à `>=4.0,<4.1` dans `backend/pyproject.toml`.

## Dette résiduelle

1. **Deux stores utilisateurs** (ADR-SEC-01) : `identity_platform` (RBAC/
   OIDC/MFA riches, en mémoire) reste non branché sur l'auth réelle.
   Réconciliation à faire dans un sprint dédié — ne pas faire les deux à
   la fois reste la bonne règle.
2. **RBAC non généralisé** : `require_role`/`require_scope` ne couvrent
   que deux routes (`identity-platform/dashboard`,
   `.../security-events`) à titre de démonstration du pattern.
3. **Périmètre de l'enforcement** : `dependencies=[Depends(
   get_current_principal)]` protège tout `/api/v1` (`api_router`). Les
   routeurs montés directement sur `app` en dehors de `/api/v1`
   (`platform_router` — métriques Prometheus et probes Kubernetes
   liveness/readiness, volontairement publics — `cloud_operations_router`,
   `runtime_platform_router`) ne sont **pas** couverts par ce sprint : ce
   sont des routeurs opérationnels, hors périmètre explicite de la
   consigne (« au niveau de l'api_router agrégateur »). Étendre
   l'authentification à `cloud_operations`/`runtime_platform` (en
   préservant les probes k8s publiques) est une dette à documenter pour
   un sprint suivant.
4. **MFA/WebAuthn, fédération OIDC/SAML complète, migration persistante
   des modules in-memory** : explicitement hors périmètre (voir consigne
   du sprint), inchangés.
5. **Vulnérabilités de dépendances transitives** (pip-audit, ~77 CVE sur
   14 paquets — `langgraph`, `starlette`, `pypdf`, `pillow`, `urllib3`,
   ...) : pré-existantes, indépendantes de ce sprint, non bloquantes en
   CI (`continue-on-error: true`). Un sprint de mise à jour de
   dépendances est recommandé séparément.
6. **`UP042` (ruff)** : 76 occurrences pré-existantes de `class X(str,
   Enum)` à travers le dépôt (ex. `Role`, `CaseStatus`), flaguées par une
   règle ruff qui préfère `enum.StrEnum`. Confirmé identique sur la
   branche avant ce sprint (`git stash` + `ruff check` : 76 erreurs des
   deux côtés) — dette pré-existante, aucun fichier de ce sprint concerné.

## Résultats qualité

- **Tests** : 2 329 passés, 7 skippés, 0 échec (`pytest`, sqlite éphémère
  en local ; Postgres en CI).
- **Couverture** : 96,09 % (seuil CI 90 %). Nouveaux modules : `core/
  security.py` 100 %, `api/v1/auth/*` 100 %, `api/v1/case/routes.py`
  100 %, `api/v1/router.py` 100 %, `application/identity/commands.py`
  98 %, `core/config.py` 98 %, `api/deps.py` 86 %, `core/tenancy.py`
  88 %, `infrastructure/persistence/repositories.py` 94 %.
- **`grep -rn "Header(...)" backend/src | grep -i firm`** → 0 résultat.
- **`bandit -r src -ll`** : aucun problème (Medium/High). En incluant les
  `Low` (informationnel, non bloquant en CI) : 21 pré-existants
  (`assert` hors tests, un faux positif `hardcoded_password_string` sur
  la valeur d'enum `"secret.manage"`) — aucun dans les fichiers de ce
  sprint.
- **`pip-audit`** : ~77 CVE sur 14 paquets transitifs, pré-existantes
  (voir dette résiduelle §5).
- **`ruff check`** : 76 erreurs `UP042` pré-existantes (dette résiduelle
  §6), 0 nouvelle erreur introduite par ce sprint.
- **`mypy`** : environnement de ce bac à sable configuré avec un `mypy`
  isolé (`uv tool`) sans accès à `fastapi`/`pydantic`/`sqlalchemy`/`jose`
  installés — cascade ~980 faux `import-not-found`, identique avant/après
  ce sprint (`git stash` : 981 avant, 979 après ce sprint). Aucune anomalie
  de typage propre au nouveau code au-delà de cette cascade.

## Documentation mise à jour

- `docs/07-strategie-securite.md` : modèle default-deny (ADR-SEC-02),
  diagrammes Mermaid (flux d'application + séquence de token), référence
  `/auth`, garde d'isolation `scoped_query`, RBAC minimal, dette des deux
  stores utilisateurs (ADR-SEC-01).
- `backend/.env.example` : secret JWT de dev documenté avec un
  commentaire expliquant le fail-fast et comment générer un vrai secret.
- `.github/workflows/ci.yml` : `TMIS_JWT_SECRET_KEY` ajouté à l'environnement
  du job `backend` (le fail-fast du Sprint sinon empêcherait tout — CI
  n'est pas en mode debug).
- Ce rapport (`docs/reports/sprint-45-rapport-securite.md`).

## Proposition du sprint suivant

**Recommandé : tranche verticale persistante `cases → drafting`** —
poursuivre la bascule entamée par les Sprints 26+ (SQLAlchemy pour
`case_intelligence`, `document_intelligence`, `legal_drafting`, ...) sur
un chemin de bout en bout cohérent, maintenant que l'authentification
réelle existe pour le protéger. En parallèle ou juste après : réconcilier
les deux stores utilisateurs (dette §1) avant que `identity_platform`
grossisse encore, et étendre le RBAC (`require_role`/`require_scope`) aux
routes d'administration `business_platform`/`ai_governance` qui en
manquent encore.
