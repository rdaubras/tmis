# Axes d'amélioration proposés pour le Sprint 12

## Dette technique assumée par conception (Sprint 11)

| Élément | Limite | Impact | Sprint suggéré |
|---|---|---|---|
| `NegotiationEngine` | Structurel uniquement — n'orchestre pas de dialogue réel entre agents en désaccord | Un désaccord persistant est signalé mais jamais "débattu" automatiquement | Sprint dédié à l'enrichissement du Consensus/Negotiation |
| `memory` (`InMemoryAgentMemoryStore`) | Process-local, non persistant | La mémoire longue d'un agent ne survit pas à un redémarrage | Aligné sur le calendrier de persistance du reste de TMIS (Sprint 13, Module Document) |
| `marketplace` | Aucun agent tiers réel publié — architecture seule | Pas de découverte d'agents en dehors du catalogue par défaut | Une fois un premier partenaire agent identifié |
| Exécution intra-mission | Séquentielle, même pour des sous-tâches indépendantes | Pas de gain de temps latence sur un futur gabarit à embranchements | Quand un gabarit non-linéaire sera introduit |
| `apply_human_decision` | `APPROVE`/`MODIFY_PLAN` sans mutation structurelle | Une modification de plan libre n'est pas encore actionnable via l'API | Sprint 12 (voir ci-dessous) |

## Axes proposés

1. **Édition de plan par l'humain** — aujourd'hui, `modify_plan` n'est
   qu'historisé. Le Sprint 12 pourrait permettre d'ajouter/retirer une
   sous-tâche du plan avant relance, pas seulement de rejouer une étape
   existante.
2. **Parallélisation intra-mission** — brancher
   `tmis.platform.performance.bounded_gather` (Sprint 10) dans
   `CoordinatorEngine.run_mission` pour exécuter concurremment les
   sous-tâches d'un même "niveau" de dépendance, une fois qu'un gabarit
   non linéaire existera (ex. RGPD et fiscal en parallèle avant
   convergence sur le raisonnement).
3. **Négociation multi-tours réelle** — faire dialoguer les agents en
   désaccord en leur donnant connaissance des positions adverses, avec
   un nombre de tours borné, avant de conclure à un désaccord
   persistant.
4. **Premier agent marketplace réel** — valider l'architecture de
   découverte/versionnement/dépendances/abonnement avec un agent
   concret plutôt que le catalogue par défaut uniquement.
5. **Mémoire persistante** — brancher `AgentMemoryPort` sur un stockage
   réel dès que la persistance générale de TMIS (Sprint 13) est en
   place.
6. **Propagation du contexte dossier** — `AgentInput.case_id` n'est
   jamais renseigné par le Coordinateur aujourd'hui (limite héritée du
   Sprint 1 : `case_id` est un `uuid.UUID`, alors que `CaseProfile.case_id`
   est une chaîne depuis le Sprint 4). Faire le lien entre une mission
   AI Team et un `CaseProfile` réel permettrait à un agent d'accéder à
   la chronologie, aux faits et aux preuves du dossier plutôt qu'au
   seul résumé textuel fourni à la création de la mission.

Ces axes sont des propositions, pas des engagements — la priorisation
reste à valider avant le Sprint 12.
