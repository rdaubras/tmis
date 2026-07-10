# Guide — Administration

## Gestion des cabinets

```python
from tmis.cabinet_os.administration.engine import AdministrationEngine
from tmis.cabinet_os.administration.schemas import FirmStatus

firm = administration.register_firm("Cabinet Durand")
administration.set_firm_status(firm.id, FirmStatus.SUSPENDED)
administration.list_firms()
```

`FirmRecord` est délibérément minimal (nom, statut, date de création)
— l'agrégat `Firm` complet (adresse de facturation, entité juridique,
image de marque) appartient au futur sprint Identity & Firm ; ce n'est
pas son remplaçant, juste ce qu'il faut au portail d'administration
pour lister et suspendre des tenants dès aujourd'hui.

## Gestion des abonnements et des utilisateurs : pas de réimplémentation

Le portail d'administration ne réimplémente ni les abonnements
(`tmis.cabinet_os.subscriptions`, voir docs/39-cabinet-os.md) ni la
gestion des membres (`tmis.collaboration.members`, Sprint 8) — il les
compose directement, chacun via son propre moteur, plutôt que de
dupliquer leur logique.

## Catalogue des connecteurs

```python
administration.register_connector("legifrance", "legal_research")
administration.set_connector_enabled("legifrance", False)
administration.list_connectors()
```

C'est un tableau de bord de métadonnées : les implémentations réelles
des connecteurs vivent dans leurs moteurs respectifs (ex.
`tmis.legal_research.connectors`) — ce registre suit seulement
lesquels sont connus et activés à l'échelle de la plateforme.

## Configuration globale

```python
administration.set_global_config("maintenance_mode", "false")
administration.get_global_config("maintenance_mode", default="false")
```

Distincte de `tmis.cabinet_os.settings` (paramètres **par cabinet**) —
la configuration globale s'applique à tous les cabinets.

## Journal d'audit

Le journal d'audit n'est pas reconstruit ici : le portail
d'administration s'appuie sur `tmis.collaboration.audit.AuditTrail`
(Sprint 8), qui trace déjà acteur, horodatage, adresse IP, action et
état avant/après.

## Monitoring : architecture seulement

```python
from tmis.cabinet_os.administration.monitoring import StaticMonitoringAdapter

snapshot = administration.monitoring_snapshot()
# cpu_percent, memory_percent, latences p50/p95, taux d'erreur — à zéro
```

`StaticMonitoringAdapter` est un stub qui renvoie des valeurs à zéro
plutôt que des chiffres inventés, en attendant un exportateur réel
(Prometheus/OpenTelemetry) — voir Sprint 28 "Observabilité complète".
Remplacer l'adaptateur ne change rien pour les appelants de
`MonitoringPort`.
