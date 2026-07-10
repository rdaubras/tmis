# Guide — Calendrier

## Un seul calendrier, plusieurs types d'événements

`tmis.cabinet_os.calendar.schemas.CalendarEventType` : `HEARING`,
`APPOINTMENT`, `CALL`, `DEADLINE`, `REMINDER`. Tous partagent le même
`CalendarEvent` — pas de table séparée par type.

```python
from tmis.cabinet_os.calendar.engine import ConfigurableCalendarEngine
from tmis.cabinet_os.calendar.schemas import CalendarEventType
from tmis.cabinet_os.calendar.store import InMemoryCalendarStore

calendar = ConfigurableCalendarEngine(InMemoryCalendarStore())
event = calendar.schedule(
    "firm-1", CalendarEventType.APPOINTMENT, "RDV client", starts_at,
)
calendar.reschedule(event.id, new_starts_at)
calendar.cancel(event.id)
```

## Les quatre vues

```python
from tmis.cabinet_os.calendar.schemas import CalendarView

calendar.view("firm-1", CalendarView.DAY, reference_date)
calendar.view("firm-1", CalendarView.WEEK, reference_date)    # lundi -> dimanche
calendar.view("firm-1", CalendarView.MONTH, reference_date)
calendar.view("firm-1", CalendarView.AGENDA, reference_date)  # tout le futur, trié
```

Chaque vue est calculée à la lecture à partir du même stockage — il
n'y a pas de vue matérialisée séparément à tenir à jour.

## Audiences : le calendrier comme source de vérité du "quand"

`hearings.HearingEngine` ne maintient pas sa propre date : planifier
une audience crée l'événement de calendrier correspondant (et un
rappel, par défaut un jour avant) via `CalendarEnginePort` :

```python
from tmis.cabinet_os.hearings.engine import HearingEngine

hearings = HearingEngine(hearing_store, calendar)
hearing = hearings.schedule(
    "firm-1", case_id, "TJ Paris", "1ere chambre", scheduled_at,
)
# hearing.calendar_event_id et hearing.reminder_event_id sont renseignés
```

Pour désactiver le rappel automatique : `reminder_before=None`.

```python
hearings.record_decision(hearing.id, "Renvoi au 15 septembre")
hearings.add_preparatory_document(hearing.id, document_id)
```

## Délais : aucune règle par défaut

`deadlines.ConfigurableDeadlineEngine` ne calcule rien tant qu'aucune
règle n'est enregistrée pour le type de procédure concerné :

```python
from tmis.cabinet_os.deadlines.engine import ConfigurableDeadlineEngine
from tmis.cabinet_os.deadlines.schemas import DeadlineCandidate

class ThirtyDayAppealRule:
    def compute(self, trigger_label, trigger_at):
        return [DeadlineCandidate(
            label=f"Appel — {trigger_label}",
            due_at=trigger_at + timedelta(days=30),
            alert_offsets=[timedelta(days=5)],
        )]

deadlines = ConfigurableDeadlineEngine(deadline_store)
deadlines.register_rule("civil_appeal", ThirtyDayAppealRule())
deadlines.compute_from_event("firm-1", case_id, "civil_appeal", "jugement", judgment_date)
```

Une procédure sans règle enregistrée produit une liste vide — jamais
une erreur — pour que l'ajout de nouvelles procédures/juridictions
reste sans risque pour l'existant.

```python
deadlines.list_upcoming("firm-1", timedelta(days=30))
deadlines.list_due_alerts("firm-1", now)  # alertes à déclencher maintenant
deadlines.mark_done(deadline_id)
deadlines.mark_missed(deadline_id)
```
