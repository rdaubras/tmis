# Guide des Playbooks (Sprint 12)

## Rôle

`tmis.cabinet_knowledge.playbooks` mémorise la façon dont un cabinet
traite un type de dossier récurrent — ouverture d'un dossier
prud'homal, création d'une société, recouvrement de créances,
contentieux commercial — et permet de suivre l'avancement d'un
playbook appliqué à un dossier réel.

## Modèle

```python
Playbook(
    id, case_type, title,
    steps: tuple[PlaybookStep, ...],
    checklist: tuple[str, ...],
)
PlaybookStep(order, title, description, documents, risks, vigilance_points)
```

Un `Playbook` est stocké comme un `KnowledgeObject` de type
`PLAYBOOK` — `playbooks/schemas.py` fournit les fonctions
`playbook_to_content()`/`playbook_from_knowledge_object()` qui
sérialisent/désérialisent les étapes dans le `content` libre du
`KnowledgeObject`.

## Cycle de vie complet

```python
playbooks = get_playbook_engine()

playbook = playbooks.create_playbook(
    firm_id, "Ouverture prud'homale", "prudhommes",
    steps=(
        PlaybookStep(1, "Entretien client", "Recueillir les faits"),
        PlaybookStep(2, "Constitution du dossier", "Rassembler les pièces"),
    ),
    checklist=("Vérifier le délai de prescription",),
    author="avocat1",
)

# 1. Validation humaine obligatoire (voir docs/62-guide-gouvernance.md)
request = get_validation_engine().submit_for_validation(firm_id, playbook.id, "avocat1")
get_validation_engine().decide(firm_id, request.id, ValidationDecision.APPROVE, "associe1")
get_approval_engine().publish(firm_id, playbook.id, "associe1")

# 2. Application à un dossier réel — refusée tant que le playbook n'est pas VALIDATED
instance = playbooks.start_instance(firm_id, playbook.id, case_reference="dossier-123")

# 3. Suivi de la progression
playbooks.complete_step(firm_id, instance.id, step_order=1)
playbooks.complete_step(firm_id, instance.id, step_order=2)
playbooks.progress(firm_id, instance.id)   # 1.0
```

`start_instance` lève `PlaybookNotValidatedError` si le playbook n'est
pas `VALIDATED` — un playbook en brouillon ne peut jamais être appliqué
à un vrai dossier. Chaque instanciation appelle
`KnowledgeSpace.record_usage()`, alimentant le score de qualité
(dimension "fréquence d'utilisation", voir docs/62-guide-gouvernance.md)
et les statistiques d'évaluation du cabinet.

## API

| Endpoint | Rôle |
|---|---|
| `POST /cabinet-knowledge/playbooks` | créer (statut `DRAFT`) |
| `GET /cabinet-knowledge/playbooks` | lister, filtrable par `case_type` |
| `GET /cabinet-knowledge/playbooks/{id}` | détail |
| `POST /cabinet-knowledge/playbooks/{id}/instances` | instancier sur un dossier (validé requis) |
| `POST /cabinet-knowledge/playbook-instances/{id}/steps/{order}/complete` | cocher une étape |

## Limite assumée ce sprint

Une instance de playbook n'est pas encore reliée à un vrai
`CaseProfile` (Sprint 4) — `case_reference` reste une chaîne libre.
Le lien structurel entre une instance de playbook et un dossier réel
est un axe proposé pour le Sprint 13 (voir le rapport d'axes
d'amélioration).
