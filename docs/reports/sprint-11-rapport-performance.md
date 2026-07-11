# Rapport de performance — Sprint 11 (AI Team Platform)

## Mesures (fournisseur echo, sans appel réseau réel — voir limite ci-dessous)

| Gabarit | Sous-tâches | Durée totale | Durée/sous-tâche |
|---|---|---|---|
| `quick_review` | 2 | 0,67 ms | 0,34 ms |
| `drafting_only` | 2 | 0,44 ms | 0,22 ms |
| `standard_analysis` | 4 | 1,17 ms | 0,29 ms |
| `full_case_analysis` | 7 | 1,83 ms | 0,26 ms |

20 missions `full_case_analysis` lancées concurremment (`asyncio.gather`) :
**31,25 ms au total**, soit environ 1,6 ms par mission en moyenne malgré
l'exécution concurrente — confirme que le Coordinateur ne sérialise pas
inutilement des missions indépendantes.

**Limite de cette mesure** : le fournisseur IA par défaut (Sprint 2)
retourne un écho déterministe sans appel réseau — ces chiffres mesurent
le coût de l'orchestration (délégation, file de travail, filtrage de
contexte, journalisation, métriques), pas la latence d'un vrai modèle.
En production, la latence dominante sera celle du fournisseur LLM
(typiquement 1 à 10 secondes par appel), pas celle du Coordinateur.

## Ce que l'orchestration coûte réellement

Le surcoût mesuré (~0,2 à 0,35 ms par sous-tâche) couvre :

- construction du contexte filtré (`ContextEngine.build_context_for`) ;
- délégation et journalisation (`DelegationEngine`, log structuré) ;
- transition d'état de la file de travail (`WorkQueue.mark_running`/
  `mark_done`) ;
- enregistrement de métrique (`MetricsCollector.record_agent_run` +
  deux écritures Prometheus).

Négligeable face à la latence d'un vrai appel LLM — aucune
optimisation de ce chemin n'est nécessaire ce sprint.

## Parallélisation

Le Coordinateur exécute les sous-tâches d'une mission **séquentiellement
dans l'ordre de dépendance** (une boucle `while True` unique dans
`run_mission`) — deux sous-tâches indépendantes du même plan (aucune
dépendance entre elles) ne sont donc pas encore parallélisées au sein
d'une même mission, seulement entre missions différentes (le test des
20 missions concurrentes le confirme). C'est une limite volontaire de
ce sprint : la plupart des gabarits actuels (`MISSION_TEMPLATES`) sont
des chaînes strictement linéaires, donc rien n'est perdu à ce stade —
mais un futur gabarit à embranchements (ex. recherche juridique et
analyse RGPD en parallèle) bénéficierait de
`tmis.platform.performance.bounded_gather` (Sprint 10) pour exécuter
les sous-tâches sans dépendance mutuelle concurremment.

## Tests de charge

Les tests d'intégration (`tests/integration/ai_team/`) couvrent
l'exécution de bout en bout des 4 gabarits, la reprise après échec
transitoire, l'échec permanent, une équipe incomplète, et le rejeu
d'une étape via le Human Loop — 18 scénarios, tous exécutés en moins
de 2 secondes au total.

## Recommandation pour le Sprint 12

Mesurer la latence réelle une fois un vrai fournisseur LLM branché
(hors périmètre de ce sprint) et envisager la parallélisation
intra-mission des sous-tâches indépendantes si un gabarit à
embranchements est introduit.
