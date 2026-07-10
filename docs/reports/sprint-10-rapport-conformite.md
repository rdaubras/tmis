# Rapport de conformité — Sprint 10 (Enterprise Platform)

## Périmètre livré

`tmis.platform.compliance.ComplianceEngine` fournit les briques
génériques exigées par le sprint, composées sans jamais connaître la
forme d'une entité métier :

| Exigence du sprint | Mécanisme livré |
|---|---|
| Export des données | `export_subject_data` — agrège chaque `DataSourceCollectorPort` enregistré en `DataExportBundle` |
| Suppression des données | `delete_subject_data` — rapporte séparément les sources réussies (`deleted_from`) et échouées (`failed_sources`), jamais un booléen global masquant un échec partiel |
| Durées de conservation | `RetentionPolicy` + `is_past_retention` — sans politique enregistrée, retourne toujours `False` ("conserver indéfiniment"), un choix conservateur explicite |
| Journalisation des accès | `log_access`/`access_log_for_subject` — distinct de `tmis.collaboration.audit.AuditTrail` (Sprint 8), scopé spécifiquement aux accès aux données personnelles |
| Registre des traitements configurable | `ProcessingRegisterEntry`/`register_processing_activity` — un registre ouvert, pas une liste figée dans le code |
| Gestion des consentements | `ConsentRecord` — jamais supprimé, seulement complété ; `has_consent` retient le dernier enregistrement par (sujet, finalité) |

## Isolation multi-tenant ("tests d'étanchéité")

- `tmis.platform.security.tenant_isolation.assert_tenant_isolated` —
  aide de test appelée dans
  `tests/integration/platform/test_platform_tenant_isolation_integration.py`
  contre `cabinet_os.clients.InMemoryClientStore.list_for_firm` et
  `collaboration.workspace.InMemoryWorkspaceStore.list_for_firm`.
- Un test négatif de contrôle (`test_assert_tenant_isolated_catches_a_deliberately_broken_query`)
  prouve que l'aide détecte effectivement une requête cassée, plutôt que
  de réussir trivialement sur n'importe quelle entrée.
- `tmis.platform.audit.PermissionAuditEngine.audit_workspace` détecte la
  seule anomalie livrée ce sprint : un rôle `CLIENT` (lecture seule par
  conception) ayant reçu des permissions supplémentaires via un
  override.

## Ce qui reste à faire (limite assumée)

- **Aucun `DataSourceCollectorPort` n'est encore enregistré en
  production** par `cabinet_os`/`collaboration` : le moteur de
  conformité est prêt et testé, mais le branchement des collecteurs
  réels (clients, documents, temps passé...) est un travail
  d'intégration distinct, non couvert par ce sprint. Sans collecteurs
  enregistrés, `export_subject_data`/`delete_subject_data` retournent
  des résultats vides plutôt que d'échouer — comportement correct mais
  qui doit être communiqué clairement à tout cabinet pilote avant mise
  en production réelle.
- Registre des traitements et politiques de conservation en mémoire
  uniquement — persistance à venir en même temps que le reste de TMIS
  (Sprint 13 "Module Document" de la roadmap révisée).
- Aucune revue juridique externe des mentions RGPD n'a été menée à ce
  stade — prévue au Sprint 30 "Durcissement pré-lancement".
