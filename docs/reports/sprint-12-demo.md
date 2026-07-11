# Démonstration — Sprint 12 (Cabinet Knowledge Engine)

## Comment la rejouer

```bash
cd backend
source .venv/bin/activate
python -m scripts.demo_cabinet_knowledge
```

Le script (`backend/scripts/demo_cabinet_knowledge.py`) compose
uniquement `tmis.cabinet_knowledge` avec des données fictives pour le
cabinet de démonstration `firm-demo` (« Cabinet Démo Lefèvre &
Associés », déjà utilisé par `seed_beta_pilot.py` au Sprint 10) — deux
utilisateurs fictifs, Julien Moreau (associé, valide) et Sarah Nguyen
(collaboratrice, propose). Rien n'est écrit dans une vraie base ;
chaque store est l'implémentation en mémoire déjà utilisée par les
tests.

## Ce que la démonstration parcourt

1. **Playbook** — création (brouillon) d'un playbook « Ouverture d'un
   dossier prud'homal » à deux étapes, avec risques et documents ;
   soumission par la collaboratrice, validation par l'associé,
   publication ; instanciation sur un dossier fictif
   (`dossier-rousseau-2026`) et progression suivie étape par étape.
2. **Clause** — clause de non-concurrence avec référence
   jurisprudentielle, même cycle validation → publication.
3. **Modèle cabinet** — un modèle de mise en demeure référençant le
   `DocumentType.MISE_EN_DEMEURE` du Sprint 7 (laissé en brouillon
   pour montrer qu'un objet non validé reste invisible des
   recommandations, voir plus bas).
4. **Pattern de raisonnement** — un schéma réutilisable sur la
   prescription en matière de contestation de licenciement.
5. **Bonne pratique** et **retour d'expérience** — deux connaissances
   type "leçon apprise" d'un dossier antérieur.
6. **Style rédactionnel** — expressions favorites et signature du
   cabinet ; une fois validé, `apply_style()` ajoute automatiquement
   la signature à un texte qui ne l'a pas déjà.
7. **Taxonomie** — interrogation des catégories du domaine social
   (arbre par défaut livré avec le sprint).
8. **Retour utilisateur** — un retour `ACCEPT` sur la clause.
9. **Score de qualité** — calcul et persistance du score de la clause.
10. **Traçabilité** — `LineageEngine.explain()` sur le playbook :
    version courante + historique complet des transitions de
    gouvernance, avec l'acteur de chaque étape.
11. **Recommandations** — recherche par mots-clés
    (`"prescription"`, `"prud'homal"`) ; seul le playbook publié
    remonte (le modèle de mise en demeure, resté en brouillon, n'est
    **jamais** recommandé), avec une explication lisible.
12. **Évaluation** — statistiques agrégées du cabinet : total,
    répartition par statut, taux de validation, score qualité moyen,
    taux d'acceptation des retours.

## Extrait de sortie réelle (exécution du 2026-07-11)

```
=== Cabinet Knowledge Engine — démonstration pour Cabinet Démo Lefèvre & Associés ===

--- Playbook : ouverture d'un dossier prud'homal ---
  Créé (brouillon) : Ouverture d'un dossier prud'homal — 2 étapes
  -> validé par Julien Moreau puis publié : Ouverture d'un dossier prud'homal
  Instancié sur le dossier 'dossier-rousseau-2026' — progression : 50%

--- Clause : non-concurrence ---
  Créée (brouillon) : Clause de non-concurrence standard
  -> validé par Julien Moreau puis publié : Clause de non-concurrence standard

--- Style rédactionnel du cabinet ---
  -> validé par Julien Moreau puis publié : Profil de style rédactionnel du cabinet
  Texte stylé : 'Cher Monsieur,\n\nBien cordialement,\nCabinet Démo Lefèvre & Associés'

--- Traçabilité (lineage) ---
  Playbook version 1, 2 évènement(s) de gouvernance
    draft -> in_review par Sarah Nguyen
    in_review -> validated par Julien Moreau

--- Recommandations pour un nouveau dossier social ---
  [playbook] Ouverture d'un dossier prud'homal (score 0.50) — mots-clés en commun : prescription, prud'homal

--- Évaluation globale du cabinet ---
  Total connaissances : 7
  Répartition par statut : {'validated': 3, 'draft': 4}
  Taux de validation : 43%
  Score qualité moyen : 0.11
  Taux d'acceptation des retours : 100%
```

(Les lignes de journalisation structurée `structlog` — un
enrichissement, une validation, une réutilisation, une recherche et
une recommandation observés en direct — ont été omises ici pour la
lisibilité ; elles apparaissent en exécutant le script.)

## Ce que cette exécution démontre concrètement

- Un objet **non validé** (le modèle de mise en demeure, resté en
  `DRAFT`) est bien invisible des recommandations, alors qu'il partage
  les mêmes mots-clés potentiels — la contrainte "validation humaine
  obligatoire avant toute réutilisation" fonctionne de bout en bout,
  pas seulement au niveau des types.
- Le score qualité moyen du cabinet (0,11) reste bas malgré 3 objets
  validés sur 7, parce que la dimension "fraîcheur"/"usage" démarre à
  zéro pour un cabinet neuf — cohérent avec le rôle du score qualité
  (encourager l'enrichissement continu, pas une note figée à la
  création).
- La traçabilité (`lineage`) restitue exactement qui a soumis puis qui
  a validé, avec les acteurs et les statuts intermédiaires — la
  réponse directe à l'exigence "chaque connaissance doit pouvoir
  expliquer son origine, les validations, les révisions, les
  versions".
