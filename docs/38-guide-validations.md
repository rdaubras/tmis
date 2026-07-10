# Guide — Validations (Approval Engine)

## Modes de validation

`tmis.collaboration.approvals.schemas.ApprovalMode` :

- `SINGLE` (« validation simple ») : un seul approbateur désigné qui
  décide `APPROVE` suffit à faire passer la demande à `APPROVED`.
- `MULTIPLE` (« validation multiple ») : **chaque** approbateur désigné
  doit avoir `APPROVE` comme dernière décision pour que la demande
  passe à `APPROVED`.

## Décisions possibles

`ApprovalDecisionType` : `APPROVE`, `REJECT`, `REQUEST_CHANGES`
(demande de modification). **Un refus ou une demande de modification
l'emporte toujours**, quel que soit le mode — même si d'autres
approbateurs ont déjà approuvé en mode `MULTIPLE`, un seul `REJECT`
fait passer la demande à `REJECTED`.

## Demander et décider

```python
from tmis.collaboration.approvals.engine import ApprovalEngine
from tmis.collaboration.approvals.schemas import ApprovalDecisionType, ApprovalMode
from tmis.collaboration.approvals.store import InMemoryApprovalStore

engine = ApprovalEngine(InMemoryApprovalStore())
approval = engine.request(
    workspace_id, "document", document_id, requested_by, ["approver-1", "approver-2"],
    ApprovalMode.MULTIPLE,
)
engine.decide(approval.id, "approver-1", ApprovalDecisionType.APPROVE)
engine.decide(approval.id, "approver-2", ApprovalDecisionType.APPROVE)
# approval.status is ApprovalStatus.APPROVED
```

Décider avec un membre absent de `approver_ids` lève `ValueError` —
seuls les approbateurs désignés à la création de la demande peuvent
se prononcer.

## Historique : jamais écrasé

Chaque décision est **ajoutée** à `ApprovalRequest.history` — y compris
lorsqu'un approbateur change d'avis (une demande de modification suivie
d'une approbation, par exemple). Le statut courant est **recalculé**
à partir de la dernière décision de chaque approbateur ; l'historique,
lui, garde la trace complète de chaque avis exprimé, dans l'ordre.

## Où l'API l'expose

- `POST /api/v1/collaboration/approvals` — demande une validation.
- `POST /api/v1/collaboration/approvals/{id}/decide` — enregistre une
  décision (`400` si l'appelant n'est pas un approbateur désigné).
- `GET /api/v1/collaboration/approvals/{id}` — consulte le statut
  courant et les approbateurs.
