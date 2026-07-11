# Guide — Audit IA

`tmis.ai_governance.audit.AIAuditEngine` est le journal spécialisé
des activités IA d'un cabinet — distinct de
`tmis.collaboration.audit.AuditTrail` (activité de workspace
générique) et de `tmis.platform.compliance.AccessLogEntry` (accès aux
données personnelles, RGPD).

## Enregistrer une entrée

```python
from tmis.ai_governance.bootstrap import get_ai_audit_engine

engine = get_ai_audit_engine()
engine.record(
    "firm-123",
    "prod-1",
    "user-1",
    "draft_generated",
    prompt="prompt-analyse-bail-v3",
    model_name="claude-legal",
    cost_usd=0.03,
    duration_ms=1450,
    decision_id="dec-1",
    policy_ids=("gpol-1",),
    validation_id="val-1",
)
```

## Ce qui est conservé

Conformément à l'énoncé du sprint : prompts, modèles, coûts, temps,
décisions, politiques appliquées, validations — chaque
`AIAuditEntry` peut référencer un `decision_id`, un ou plusieurs
`policy_ids`, et un `validation_id`, reliant l'entrée d'audit à
`decision_records`, `policy_engine` et `human_validation`.

## Consulter

```python
engine.list_for_firm("firm-123")
engine.list_for_production("firm-123", "prod-1")
```

## Exporter

```python
csv_text = engine.export_csv("firm-123")
```

Exposé également via `GET /api/v1/ai-governance/audit/export
?firm_id=...`, qui retourne un fichier `text/csv` téléchargeable
directement.
