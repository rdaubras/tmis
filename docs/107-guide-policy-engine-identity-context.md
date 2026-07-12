# Guide — Policy Engine & Identity Context (Sprint 19)

## Identity Context — le profil métier de l'utilisateur

`identity_context.IdentityContext` porte tout ce que les agents IA et
le moteur d'autorisation ont besoin de connaître sur un utilisateur
pour la durée d'une requête : spécialité juridique, niveau
d'expérience, ancienneté, équipe, département, langue, préférences
rédactionnelles, modèles IA autorisés, droits de validation, politiques
applicables.

```python
identity_context.set_context(IdentityContext(
    user_id="user-1", firm_id="firm-1",
    specialty="corporate", experience_level="senior", seniority_years=6,
    team_id="team-ma", department_id="dept-corp",
    can_validate=True,
))
```

`authorization.AuthorizationEngine.check` lit `IdentityContext.
team_id`/`department_id`/`seniority_years`/`experience_level` pour
évaluer ABAC et les politiques restreintes à une équipe — **jamais un
champ de la requête HTTP** (voir `api.routes.check_authorization` :
seul `confidentiality_level`/`resource_department_id`, des attributs
de la *ressource* accédée, transitent par requête ; les attributs de
l'*identité* viennent du contexte persisté via `PUT
/identity-platform/identity-context`).

Les agents IA lisent ce même contexte pour adapter leurs propositions
(modèle autorisé, ton, langue) — c'est le mécanisme par lequel un
futur agent respecte les préférences et droits du cabinet sans logique
ad hoc.

## Policy Engine — politiques configurables par cabinet

Voir docs/105-guide-rbac-abac-zero-trust.md pour le rôle du
`PolicyEngine` dans la chaîne Zero Trust. Ce guide couvre la
configuration :

```python
policies.create(
    firm_id, Permission.STRATEGY_DRAFT_VALIDATE,
    requires_second_validation=True,
    reason="brouillon stratégique : double validation requise",
)
policies.create(
    firm_id, Permission.AI_MODEL_RESTRICTED_USE,
    allowed_roles=frozenset({Role.PARTNER}),
    reason="modèles avancés réservés aux associés",
)
policies.create(
    firm_id, Permission.EXPORT_DATA,
    denied_roles=frozenset({Role.PARALEGAL, Role.ASSISTANT}),
)
```

Une `Policy` peut être désactivée (`active=False`, non exposé côté API
ce sprint) plutôt que supprimée, pour garder un historique. Chaque
politique est scoping firm-wide : `PolicyEngine.list_active_for_firm`
n'expose jamais les politiques d'un autre cabinet — utilisé par
`monitoring.IdentityMonitoringEngine` pour le compteur
`active_policies` du tableau de bord.

`identity_platform.policy_engine.PolicyEngine` est la quatrième
occurrence de la collision `PolicyEngine`/`GovernanceEngine` — voir
docs/103-architecture-identity-platform.md pour les trois autres.
