# Guide Conformité (Sprint 10)

## Rôle du module

`tmis.platform.compliance` (`ComplianceEngine`) fournit les briques
génériques dont tout traitement de données personnelles a besoin, sans
jamais connaître la forme d'une entité métier : il compose des
`DataSourceCollectorPort` enregistrés par chaque module métier au
bootstrap, plutôt que d'interroger directement les stores de
`cabinet_os`/`collaboration`.

## Export des données (droit d'accès/portabilité)

`export_subject_data(firm_id, subject_id)` interroge chaque source
enregistrée (`collector.collect(...)`) et assemble un
`DataExportBundle` : `sections` associe un nom de source (`"clients"`,
`"documents"`, `"time_entries"`...) aux lignes qu'elle a produites.

## Suppression des données (droit à l'effacement)

`delete_subject_data(firm_id, subject_id)` demande à chaque source de
supprimer les données du sujet et rapporte séparément les sources ayant
réussi (`deleted_from`) et échoué (`failed_sources`) — jamais un simple
booléen global qui masquerait un échec partiel.

## Durées de conservation

`RetentionPolicy` associe un `entity_type` à un nombre de jours.
`is_past_retention(entity_type, age_days)` **sans politique enregistrée
retourne toujours `False`** ("conserver indéfiniment") — un choix
explicite et conservateur : l'absence de configuration ne doit jamais
être interprétée comme une autorisation de suppression automatique.

## Journalisation des accès

`log_access(firm_id, actor_id, subject_id, action)` alimente un journal
distinct de `tmis.collaboration.audit.AuditTrail` (Sprint 8) : ce
dernier trace l'activité métier générale, celui-ci trace spécifiquement
les accès aux données personnelles pour les besoins de conformité —
lecture, export, suppression (`AccessAction`).

## Registre des traitements

`ProcessingRegisterEntry` est un registre **configurable**, pas une
liste figée dans le code : un cabinet/DPO ajoute ses propres activités
de traitement (nom, finalité, catégories de données, base légale,
référence de politique de conservation, destinataires) via
`register_processing_activity`.

## Consentements

`ConsentRecord` garde chaque changement d'état (jamais de suppression) :
`has_consent` retourne le dernier enregistrement pour un couple
(sujet, finalité) — une révocation reste dans l'historique, elle
n'efface pas la trace qu'un consentement a existé.

## Ce qui reste à faire

- Aucun `DataSourceCollectorPort` n'est encore enregistré par
  `cabinet_os`/`collaboration` en production — le moteur est prêt,
  le branchement des collecteurs réels est un travail d'intégration
  ultérieur (voir rapport de dette technique).
- Le registre des traitements et les politiques de conservation sont
  en mémoire ; leur persistance suit le même calendrier que le reste de
  TMIS.
