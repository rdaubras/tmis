# Guide Bêta Pilote (Sprint 10)

## Objectif

Préparer un environnement de démonstration réaliste pour les premiers
cabinets pilotes, sans dépendre d'aucune donnée réelle de client.

## Génération des données de démonstration

```bash
cd backend
python -m scripts.seed_beta_pilot
```

Le script `backend/scripts/seed_beta_pilot.py` crée, en mémoire (aucune
écriture en base — un cabinet pilote peut le relancer sans risque) :

- **Un cabinet de démonstration** : "Cabinet Démo Lefèvre & Associés"
  (`firm_id="firm-demo"`), plan `cabinet_small` (10 utilisateurs),
  licence de démonstration signée (30 jours).
- **Des utilisateurs de démonstration** : une administratrice, deux
  collaborateurs, une assistante, un client externe — couvrant chaque
  rôle du système de permissions (`docs/34-guide-roles.md`).
- **Des clients fictifs** : personnes physiques et morales, avec
  coordonnées plausibles mais inventées.
- **Des dossiers d'exemple** : un litige commercial, un dossier de
  droit du travail, un dossier de conseil contractuel — chacun avec des
  faits, des tâches et un document brouillon associés.
- **Un parcours d'onboarding** : une checklist imprimée en sortie de
  script, pensée pour un premier contact avec la plateforme (connexion,
  création d'un dossier, invitation d'un collaborateur, génération d'un
  premier brouillon).

## Ce que ce script n'est pas

- Ce n'est **pas** un outil de seed de production — il instancie des
  stores en mémoire (`InMemory*`) exactement comme les tests
  d'intégration, pour un environnement de démonstration jetable.
- Il ne crée aucune fonctionnalité métier nouvelle : il compose
  uniquement les moteurs déjà livrés (Sprints 4, 8, 9, 10).

## Parcours d'onboarding suggéré pour un cabinet pilote

1. Se connecter avec l'utilisatrice administratrice de démonstration.
2. Consulter le tableau de bord (`cabinet_os.dashboard`) — vue
   d'ensemble des dossiers et de l'activité.
3. Ouvrir un dossier d'exemple, consulter sa chronologie
   (`case_intelligence.timeline`) et ses tâches associées.
4. Générer un brouillon de document à partir d'un modèle
   (`legal_drafting`) sur ce dossier.
5. Inviter un second utilisateur de démonstration au dossier et
   observer les permissions effectives par rôle.
6. Consulter `GET /platform/monitoring` pour voir le suivi de coût IA
   et l'état de santé de l'instance.
