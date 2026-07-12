# Démonstration — Sprint 17 : trois workflows fictifs

Script : `backend/scripts/demo_workflow_automation.py`
(`python -m scripts.demo_workflow_automation` depuis `backend/`).
Cabinet fictif : "Cabinet Démo Lefèvre & Associés — Automatisation"
(`firm-demo-alwp`), isolé des autres scripts de démonstration.

## Workflow 1 — Ouverture d'un dossier (exécution séquentielle)

Instancié depuis le modèle par défaut `ouverture_dossier`, activé,
puis exécuté sur un dossier fictif :

```
Workflow instancié : « Ouverture d'un dossier » v1, 2 étape(s)
Statut : completed
  étape 0 : Tâche créée : {}
  étape 1 : Notification envoyée
```

Chaque étape est journalisée par `action_engine`, et l'exécution
entière l'est par `audit.WorkflowAuditEngine`.

## Workflow 2 — Préparation d'une audience (règle + déclencheur)

Une règle configurable ("audience dans moins de 7 jours") est évaluée
sur un contexte fictif (J-3) avant de déclencher le workflow de
préparation — trois étapes (checklist, rappel J-3, notification de
l'avocat responsable) s'exécutent sans intervention de code :

```
Règle « Audience dans moins de 7 jours » évaluée sur J-3 : True
Statut : completed, 3 étape(s) exécutée(s)
```

## Workflow 3 — Mise en demeure (validation humaine + simulation)

Illustre l'intégralité du cycle de gouvernance d'une action critique :

1. La politique de validation est configurée pour
   `generate_draft` — vraie, donc obligatoire.
2. Une demande de validation est créée (`pending`), puis approuvée par
   un associé (réutilise `ai_governance.human_validation` sans aucune
   réimplémentation).
3. Le workflow est **simulé** avant toute exécution réelle — la
   simulation prédit que les deux étapes s'exécuteraient, sans jamais
   toucher `action_engine` :

```
Simulation : compléterait = True
  Générer le brouillon de mise en demeure : exécuterait = True
  Notifier l'avocat responsable : exécuterait = True
```

4. L'exécution réelle complète le workflow.
5. Une tentative de rollback sur l'étape "générer le brouillon" est
   journalisée comme non compensée — aucun handler de rollback n'est
   enregistré pour `generate_draft` (par construction : générer un
   brouillon n'est pas une action réversible au sens du sprint), ce
   qui démontre que `rollback.RollbackEngine` rapporte explicitement
   l'absence de handler plutôt que d'échouer silencieusement.

## Synthèse

Le journal d'audit du cabinet fictif contient une entrée par
exécution, consultable via `WorkflowAuditEngine.list_for_firm()` ou
`GET /api/v1/workflow-automation/audit`. Aucune des trois
démonstrations n'a produit de décision juridique définitive : chaque
brouillon généré reste soumis à validation humaine, conformément à la
contrainte centrale du sprint.
