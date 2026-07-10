# Rapport d'architecture — Sprint 10 (Enterprise Platform)

## Résumé

Le Sprint 10 ajoute `backend/src/tmis/platform/` (21 sous-modules) au-
dessus des neuf moteurs métier livrés depuis le Sprint 2, sans modifier
un seul de leurs schémas, ports ou moteurs. Trois fichiers existants
seulement ont été touchés par branchement : `core/logging.py` (insertion
d'un processeur de rédaction), `core/config.py` (deux nouveaux champs de
configuration), `main.py` (chaîne de middlewares + routeur `/platform`).

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque module suit
  systématiquement `schemas.py` (dataclasses sans dépendance) →
  `ports.py` (`Protocol`) → implémentation(s) → `bootstrap.py`
  (singleton `functools.lru_cache` quand un état process-wide a du
  sens). Aucune exception à ce patron sur les 21 modules.
- **Twelve-Factor App** : configuration exclusivement par variables
  d'environnement (`TMIS_*`), validée en production par
  `tmis.platform.configuration.validate_production_readiness` ; aucun
  état local requis en dehors des stores explicitement documentés comme
  temporaires (`InMemory*`, backup local).
- **Aucune fonctionnalité métier nouvelle** : vérifié — aucun nouvel
  agrégat de domaine, aucun nouveau workflow IA. Les seules "features"
  ajoutées (feature flags, licences) sont des mécanismes de
  commercialisation transverses, pas des capacités juridiques.

## Décisions structurantes

1. **Dépendances hand-roulées plutôt qu'ajoutées** quand une bibliothèque
   suffisait à un besoin déjà servi par un patron existant : l'exposeur
   Prometheus (`platform/metrics/registry.py`) suit le même choix que
   les writers PDF (Sprint 7) et XLSX (Sprint 9). À l'inverse,
   `cryptography` (déjà transitive) et `PyYAML` (nécessaire à des
   manifests Kubernetes corrects) ont été promues en dépendances
   directes plutôt que hand-roulées — la génération YAML/HMAC à la main
   aurait été plus risquée que d'ajouter une dépendance mature.
2. **Ports étroits pour éviter les dépendances circulaires** : `
   monitoring/ports.CostSummaryPort` a été défini avant que
   `cost_control/` n'existe, avec un adaptateur `NullCostSummaryPort`
   temporaire remplacé ensuite par `CostTrackerSummaryAdapter` — sans
   jamais faire dépendre `monitoring` de `cost_control` directement.
3. **Duplication délibérée et documentée** : `platform.rate_limiting`
   généralise `cabinet_os.public_api.rate_limiter` (Sprint 9) sans le
   remplacer, pour ne courir aucun risque de régression sur les tests
   déjà verts du Sprint 9 — la contrainte "toutes les fonctionnalités
   existantes restent compatibles" prime sur la suppression de
   duplication.
4. **Sémantique Kubernetes respectée** : `HealthCheckEngine.liveness()`
   ne sonde jamais une dépendance (évite qu'une panne partielle ne
   déclenche un redémarrage en cascade de tous les pods) ; seule
   `readiness()` agrège les 7 sondes.

## Vérification de non-régression

`ruff check src tests` et `mypy src` : aucune erreur sur 701 fichiers
source. `pytest` : **883 tests passés, 4 ignorés**, contre 747 avant ce
sprint — soit 136 tests dédiés à `tmis.platform` (93 % de couverture sur
ce périmètre) sans qu'aucun des 747 tests précédents n'ait été modifié
ni n'ait échoué à un quelconque moment du sprint.

## Voir aussi

`docs/46-architecture-enterprise.md` pour les diagrammes Mermaid et le
détail des paliers de déploiement (solo / cabinet 10 / cabinet 100 /
direction juridique entreprise).
