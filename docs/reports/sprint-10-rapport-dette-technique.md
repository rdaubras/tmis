# Rapport de dette technique — Sprint 10 (Enterprise Platform)

## Dette assumée par conception (documentée dans le code)

| Élément | Limite | Impact | Sprint de résolution suggéré |
|---|---|---|---|
| `CostTrackerEngine` | `TMISKernel.complete()` ne propage pas de contexte utilisateur/dossier/workflow ; aucun enregistrement de coût automatique | Le suivi de coût requiert un appel manuel `record()` par l'appelant | S16 (intégration agents métier au Kernel) |
| `compliance.ComplianceEngine` | Aucun `DataSourceCollectorPort` réel enregistré (`cabinet_os`, `collaboration`) | Export/suppression RGPD retournent des résultats vides en l'état | S24 (Sécurité renforcée & RGPD) |
| `security.sso` | Ports `OidcProviderPort`/`SamlProviderPort` définis, aucune implémentation | Pas de SSO fonctionnel avant intégration d'un fournisseur réel | S11 (Identity & Firm) |
| `security.secrets_rotation` | Store de rotation en mémoire, aucun KMS réel branché | Les clés ne survivent pas à un redémarrage de processus | S24 |
| `health.bootstrap._check_database` | Vérifie la présence de l'URL de connexion, pas une vraie requête `SELECT 1` | Un health check "ready" peut rester vert alors que la base est injoignable | S13 (Module Document + Persistance) |
| `health.bootstrap._check_storage`/`_check_queue` | Aucun client de stockage objet ni app Celery réels à sonder encore | Sondes structurelles uniquement (présence de configuration) | S13 |
| `backup`/`restore` | Implémentation de référence sur système de fichiers local uniquement | Pas d'adaptateur S3/GCS livré (le port `BackupStoragePort` est prêt) | À planifier selon le fournisseur cloud retenu |
| `monitoring.adapters.NullCostSummaryPort` | Adaptateur placeholder conservé dans le code bien que non utilisé par le bootstrap actuel | Code mort mineur, sans risque | Nettoyage mineur, non urgent |
| `rate_limiting` (duplication) | `platform.rate_limiting` généralise mais ne remplace pas `cabinet_os.public_api.rate_limiter` (Sprint 9) | Deux implémentations logiquement proches coexistent | Unifier lors d'un futur sprint de refactoring, une fois la surface d'API de `cabinet_os.public_api` stabilisée |

## Vulnérabilités de dépendances relevées par `pip-audit`

53 CVE sur 8 paquets, toutes nécessitant une montée de version
**majeure** :

| Paquet | Version installée | Versions corrigées connues |
|---|---|---|
| `starlette` | 0.46.2 | ≥ 1.0.1 (bump majeur, entraîné par `fastapi`) |
| `pypdf` | 5.9.0 | ≥ 6.8.0 (bump majeur) |
| `langgraph` | 0.2.76 | — (suivre les correctifs amont) |
| `langgraph-checkpoint` | 2.1.2 | — |
| `langgraph-sdk` | 0.1.74 | — |
| `pillow` | 10.4.0 | — |
| `pytest` | 8.4.2 | ≥ 9.0.3 (dev uniquement, risque limité) |
| `ecdsa` | 0.19.2 | — |

**Décision** : reportées sans exception à un sprint dédié. Un bump de
version majeure de `starlette`/`fastapi` ou `pypdf` change potentiellement
un comportement observable (signatures, formats d'export) et contredit
la contrainte du Sprint 10 ("toutes les fonctionnalités existantes
doivent rester compatibles", "aucune nouvelle fonctionnalité métier").
Un sprint dédié aux montées de version majeures, avec sa propre suite de
non-régression ciblée, est la voie la plus sûre.

## Dette de test

- Les modules `platform.security.sso`, `platform.rate_limiting.ports`
  et `platform.monitoring.adapters` ont une couverture de tests nulle —
  légitime : ce sont des `Protocol` purs ou un adaptateur non utilisé,
  sans branche de code exécutable à tester.
- Les fonctions `bootstrap.py` (singletons `lru_cache`) sont peu
  couvertes directement — leur comportement (composition de
  dépendances) est vérifié indirectement par les tests d'intégration
  qui les invoquent via les endpoints `/platform/*`.

## Dette de documentation

- Aucune : les 7 guides Sprint 10 (`docs/46` à `docs/52`) couvrent
  chaque module livré ; les 5 rapports de fin de sprint couvrent
  architecture, sécurité, performance, conformité et dette technique.

## Recommandation pour le Sprint 11

Le Sprint 11 (`Identity & Firm`, authentification réelle) est le point
naturel pour résorber une partie de cette dette : brancher un
fournisseur SSO réel derrière les ports déjà posés
(`security.sso`), et faire de l'authentification le premier
`DataSourceCollectorPort` réel pour `compliance.ComplianceEngine`.
