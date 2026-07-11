# Guide du Critique Engine (Sprint 11)

## Rôle

`CritiqueEngine.critique(sub_task_id, agent_id, output)` recherche les
incohérences, vérifie la présence de références, détecte les oublis
et propose des améliorations sur la production d'un agent — sans
appeler de modèle : c'est une base déterministe, exécutée sur
**chaque** production, indépendamment de la présence d'un agent
Critique dans l'équipe.

## Règles appliquées

| Vérification | Conséquence |
|---|---|
| Texte de moins de 20 caractères | `issue` : "production potentiellement incomplète" |
| Confiance `LOW` sans avertissement associé | `issue` : "confiance faible sans avertissement" |
| Aucune citation | `suggestion` : ajouter des références |
| Aucun avertissement | `suggestion` : confirmer qu'aucune réserve n'a été omise |

`Critique.is_clean` est `True` si et seulement si `issues` est vide —
les `suggestions` sont des améliorations facultatives, jamais des
motifs de rejet.

## L'agent Critique (complément fondé sur un modèle)

Au-delà de `CritiqueEngine` (règles déterministes), le catalogue
d'agents par défaut inclut un agent au rôle `AgentRole.CRITIC`
(`agent-critic`), un `PromptedTeamAgent` dont le prompt système
demande explicitement de "rechercher les incohérences, vérifier les
références citées, détecter les oublis, et proposer des
améliorations" — la critique **fondée sur un modèle** que le sprint
demande. Un plan de mission peut l'inclure via
`TaskType.CRITIQUE`/`AgentRole.CRITIC` pour une critique plus riche
que les règles déterministes seules.

## Review Engine : de la critique à une décision

`ReviewEngine.review(mission_id, sub_task_id, agent_id, output)`
transforme une `Critique` en l'une de trois décisions :

- **`APPROVED`** — critique propre (`is_clean`) ;
- **`REJECTED`** — la production semble substantiellement incomplète
  (texte trop court) ;
- **`REVISION_REQUESTED`** — tout autre problème non fatal (ex. confiance
  faible sans avertissement).

```python
record = review_engine.review("m1", "st-1", "agent-drafter", output)
record.decision   # ReviewDecision.APPROVED | REJECTED | REVISION_REQUESTED
record.critique   # la Critique complète, pour affichage détaillé
```

**Cette décision reste consultative** — `tmis.ai_team.human_loop` a
toujours le dernier mot, conformément à la contrainte du sprint selon
laquelle toute production reste une proposition soumise à validation
humaine.
