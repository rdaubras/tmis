# Guide — Multi-Tenant & Hiérarchie Organisationnelle (Sprint 19)

## La hiérarchie

Organisation → Départements → Équipes → Utilisateurs → Permissions →
Policies → Quotas → Branding. `tenant_management.
TenantManagementEngine` compose `organization`/`departments`/`teams`/
`users`/`tenant_context` — c'est le point d'entrée unique pour
provisionner et consulter cette hiérarchie ; les cinq sous-moteurs ne
doivent jamais être appelés indépendamment pour ce cas d'usage.

```python
engine.onboard_firm(
    "firm-1", "Cabinet Dupont & Associés",
    quota=TenantQuota(max_users=50),
    branding=TenantBranding(display_name="Cabinet Dupont"),
)
hierarchy = engine.hierarchy("firm-1")
# hierarchy.organization, .tenant_profile, .departments, .teams, .users
```

## Isolation multi-tenant

Chaque store est indexé par `firm_id` (souvent `(firm_id, id)` en clé
composite) : aucune requête ne peut retourner une donnée d'un autre
cabinet, y compris pour un `user_id` identique entre deux cabinets —
`identity_platform` traite `(firm_id, user_id)` comme l'identité
réelle, jamais `user_id` seul.

`tenant_context.engine` réexporte directement
`platform.security.tenant_isolation.TenantContext`/
`TenantAccessError`/`require_same_firm` (Sprint 10) plutôt que de
redévelopper la vérification de frontière tenant.

Les tests d'isolation
(`tests/integration/identity_platform/
test_identity_platform_multi_tenant_isolation_integration.py`)
démontrent que :

- deux organisations avec le même `legal_name` mais des `firm_id`
  différents restent indépendantes ;
- un rôle assigné à un `user_id` dans le cabinet A n'existe pas pour
  ce même `user_id` dans le cabinet B ;
- une autorisation accordée dans un cabinet est refusée pour le même
  utilisateur adressé sous un autre `firm_id` ;
- appareils, sessions, délégations et secrets ne sont jamais
  mélangés entre cabinets, même avec des clés identiques
  (`key="shared-key-name"` dans deux cabinets différents restent deux
  secrets distincts) ;
- le tableau de bord (`monitoring.IdentityDashboard`) n'agrège jamais
  les compteurs de deux cabinets.

## `Organization` vs `FirmRecord`

`identity_platform.organization.Organization` est la "fuller Firm
aggregate" — `cabinet_os.administration.FirmRecord` (Sprint 9) est un
enregistrement minimal (id/nom/statut) dont le docstring déférait
explicitement l'aggregate complet à ce sprint. Les deux coexistent :
`FirmRecord` reste l'enregistrement d'exploitation plateforme,
`Organization` est la racine de la hiérarchie d'identité.
