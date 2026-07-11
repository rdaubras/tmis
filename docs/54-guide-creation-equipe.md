# Guide de création d'une équipe (Sprint 11)

## Équipes prédéfinies

`tmis.ai_team.capabilities.mission_templates.MISSION_TEMPLATES` définit
quatre gabarits, chacun une séquence ordonnée de (type de tâche, rôle) :

| `case_type` | Étapes |
|---|---|
| `quick_review` | Vérification → Contrôle qualité |
| `drafting_only` | Rédaction → Vérification |
| `standard_analysis` | Analyse documentaire → Recherche juridique → Vérification → Contrôle qualité |
| `full_case_analysis` | Analyse documentaire → Recherche juridique → Jurisprudence → Raisonnement → Rédaction → Vérification → Contrôle qualité |

**Cette table est la source de vérité unique**, lue à la fois par
`TeamBuilder` (quels agents inclure dans l'équipe) et par `Planner`
(à quel agent assigner chaque sous-tâche du plan). Ne jamais dupliquer
cette liste ailleurs — une équipe composée pour un `case_type` donné
est garantie de contenir tous les rôles que le plan correspondant va
demander.

## Composer une équipe automatiquement

```python
from tmis.ai_team.teams.engine import TeamBuilder
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.ai_team.teams.schemas import MissionComplexity

team = team_builder.build_team(
    domain=LegalDomain.DATA_PROTECTION,
    complexity=MissionComplexity.HIGH,
    case_type="full_case_analysis",
    target_cost_usd=0.15,          # optionnel
    desired_delay_seconds=30.0,    # optionnel
)
```

### Expert de domaine conditionnel

Si `domain` a un expert associé (`DATA_PROTECTION` → RGPD, `FISCAL` →
fiscal, `SOCIAL` → droit social — voir
`tmis.ai_team.capabilities.catalog.domain_expert_role`) **et** que la
complexité n'est pas `LOW`, l'agent expert correspondant est
automatiquement ajouté à l'équipe — "si pertinent", comme demandé par
le sprint. Un domaine sans expert dédié (`GENERAL`, `CIVIL`,
`COMMERCIAL`, `PENAL`) n'ajoute jamais d'expert supplémentaire.

### Contrainte de coût ou de délai

`target_cost_usd`/`desired_delay_seconds` filtrent l'équipe
gloutonnement, dans l'ordre du gabarit, en conservant toujours au
moins le premier agent (une équipe n'est jamais vide). Une contrainte
trop stricte peut donc produire une équipe incomplète par rapport au
plan généré — la mission se terminera alors en `FAILED` sur les
sous-tâches dont l'équipe ne couvre pas le rôle (voir
docs/55-guide-coordinateur.md).

## Composer une équipe personnalisée

```python
team = team_builder.build_custom_team(
    name="Mon équipe sur mesure",
    agent_ids=["agent-drafter", "agent-verifier", "agent-gdpr-expert"],
)
```

Une équipe personnalisée (`is_custom=True`) n'est vérifiée contre
aucun gabarit — c'est à l'appelant de s'assurer qu'elle couvre les
rôles dont le plan aura besoin.

## API REST

```
POST /api/v1/ai-team/teams          { domain, complexity, case_type, target_cost_usd?, desired_delay_seconds? }
POST /api/v1/ai-team/teams/custom   { name, agent_ids }
```
