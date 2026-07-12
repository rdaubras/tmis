# Démo — Sprint 19 (Enterprise Identity & Trust Platform)

Démonstration exécutée via `TestClient(app)` contre l'API réelle
(`/api/v1/identity-platform`, `/api/v1/workflow-automation`) — sortie
capturée telle quelle.

## 1. Deux cabinets concurrents

```
POST /organizations {"firm_id": "cabinet-dupont", "legal_name": "Cabinet Dupont & Associés"}
POST /organizations {"firm_id": "cabinet-martin", "legal_name": "Cabinet Martin Avocats"}

Cabinet Dupont: {'firm_id': 'cabinet-dupont', 'legal_name': 'Cabinet Dupont & Associés', 'status': 'active'}
Cabinet Martin: {'firm_id': 'cabinet-martin', 'legal_name': 'Cabinet Martin Avocats', 'status': 'active'}
```

## 2. Le même `user_id`, rôle accordé dans un seul cabinet

Un rôle PARTNER est assigné à `u-42` **uniquement** chez Cabinet
Dupont. Le même identifiant utilisateur, adressé sous l'autre cabinet,
n'hérite d'aucune permission :

```
Authorized at Cabinet Dupont: {'allowed': True, 'reason': '', 'requires_second_validation': False}
Authorized at Cabinet Martin (same user_id!): {'allowed': False, 'reason': "aucun rôle de 'u-42' n'accorde consultation.validate", 'requires_second_validation': False}
```

`identity_platform` traite `(firm_id, user_id)` comme l'identité
réelle — jamais `user_id` seul.

## 3. Une politique cabinet-spécifique refuse ce que RBAC accordait

Cabinet Dupont configure : « export interdit pour les associés ce
trimestre (audit en cours) ». Le `PartnerRole` de `u-42` accordait
`export.data` via RBAC — la politique du cabinet a le dernier mot :

```
Export decision at Cabinet Dupont: {'allowed': False, 'reason': 'export gelé ce trimestre (audit en cours)', 'requires_second_validation': False}
```

## 4. Cette même politique n'affecte jamais l'autre cabinet

Cabinet Martin n'a configuré aucune politique équivalente — son propre
associé (`u-99`) garde l'accès :

```
Export decision at Cabinet Martin: {'allowed': True, 'reason': '', 'requires_second_validation': False}
```

## 5. Les secrets restent chiffrés et isolés par cabinet

Deux secrets portant la **même clé** (`crm-key`) dans deux cabinets
différents restent deux enregistrements indépendants ; l'API ne
retourne jamais le texte en clair, seulement les métadonnées :

```
Cabinet Dupont secrets (metadata only): [{'key': 'crm-key', 'firm_id': 'cabinet-dupont', 'created_at': '...', 'rotated_at': None}]
Cabinet Martin secrets (metadata only): [{'key': 'crm-key', 'firm_id': 'cabinet-martin', 'created_at': '...', 'rotated_at': None}]
```

## 6. Un module existant (`workflow_automation`) passe désormais par la plateforme

Une décision d'approbation, migrée ce sprint, est refusée pour un
utilisateur sans rôle et acceptée pour `u-42` (PARTNER chez Cabinet
Dupont) :

```
Approval decision by an unassigned user: 403 {'detail': "aucun rôle de 'someone-with-no-role' n'accorde consultation.validate"}
Approval decision by u-42 (PARTNER at Cabinet Dupont): 200 {'id': '...', 'production_id': 'action-demo', 'status': 'approved'}
```

## 7. Tableau de bord identité — jamais de fuite de compteurs entre cabinets

```
Cabinet Dupont dashboard: {'firm_id': 'cabinet-dupont', 'active_sessions': 0, 'mfa_enrolled_users': 0, 'trusted_devices': 0, 'active_delegations': 0, 'active_policies': 1, 'security_events_total': 0, 'high_risk_events_last_24h': 0}
Cabinet Martin dashboard: {'firm_id': 'cabinet-martin', 'active_sessions': 0, 'mfa_enrolled_users': 0, 'trusted_devices': 0, 'active_delegations': 0, 'active_policies': 0, 'security_events_total': 0, 'high_risk_events_last_24h': 0}
```

Cabinet Dupont affiche `active_policies: 1` (la politique d'export
gelé) ; Cabinet Martin affiche `0` — jamais mélangés.

## Conclusion

Cette démonstration couvre les deux exigences explicites de fin de
sprint : **l'isolation multi-tenant** (étapes 2, 4, 5, 7 — même
identifiant, même clé de secret, aucune fuite) et **l'application des
politiques** (étapes 3, 6 — une politique cabinet-spécifique refuse un
accès que RBAC accordait, et un module métier existant applique
désormais cette même chaîne). Script source :
`tests/integration/identity_platform/` (couverture automatisée
équivalente) et scratchpad de session pour la version scénarisée
ci-dessus.
