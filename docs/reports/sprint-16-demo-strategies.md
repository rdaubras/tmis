# Démonstration — Sprint 16 : trois dossiers fictifs, trois jeux de stratégies

Script : `backend/scripts/demo_strategic_intelligence.py`
(`python -m scripts.demo_strategic_intelligence` depuis `backend/`).
Cabinet fictif : "Cabinet Démo Lefèvre & Associés — Contentieux"
(`firm-demo-si`), isolé des autres scripts de démonstration.

## Dossier 1 — Licenciement contesté (exemple de la Vision du sprint)

Question : *"Comment défendre ce salarié ?"*

Le `strategy_engine` propose les quatre types par défaut, chacun
expliqué, avec un score de confiance et une limitation rappelant
qu'aucune n'est une décision définitive :

| Stratégie | Confiance |
|---|---|
| Négociation amiable | 0.62 |
| Action prud'homale | 0.62 |
| Stratégie transactionnelle | 0.62 |
| Stratégie procédurale | 0.62 |

Le `hypothesis_lab` compare deux hypothèses concurrentes
("licenciement sans cause réelle et sérieuse" vs. "discrimination
syndicale sous-jacente"), le `risk_matrix` évalue la première
stratégie (score 0.46, expliqué facteur par facteur),
`opportunity_engine` et `evidence_gap` identifient 2 opportunités et
1 élément de preuve manquant classé "impact élevé", et
`action_planner` construit un plan de 2 étapes entièrement modifiable.

## Dossier 2 — Résiliation de bail commercial pour impayés

Question : *"Comment sécuriser la résiliation du bail commercial ?"*

Types de stratégies **différents du Dossier 1**, démontrant que le
SLAI ne produit pas un jeu figé de stratégies mais s'adapte au
contexte via `candidate_types` :

- Commandement de payer visant la clause résolutoire
- Assignation en référé-expulsion
- Négociation d'un protocole d'accord

`tradeoffs` compare les deux premières par paire (risque partagé :
"contestation possible en référé"), `decision_support` produit un
tableau à 3 stratégies sans jamais désigner de gagnant, `timeline`
trie 3 événements chronologiquement, `probability` évalue la
recevabilité du commandement de payer comme "high" (vraisemblance
qualitative sur un sous-élément, pas sur l'issue du procès), et
`simulation` repère structurellement que les trois stratégies
référencent le mot-clé "impayés" — sans aucune prédiction d'issue.

## Dossier 3 — Litige de consommation (vice caché)

Question : *"Quelle voie privilégier pour le consommateur lésé ?"*

Un troisième jeu de stratégies encore différent :

- Médiation de la consommation
- Action en garantie des vices cachés
- Résolution amiable avec le vendeur

Le `review` (adaptateur `ai_governance.human_validation`) illustre le
cycle complet : demande de revue → statut `pending` → décision
`APPROVE` de l'associé → `is_validated` passe à `True`.

## Synthèse

```
licenciement:      ["Action prud'homale", "Négociation amiable", "Stratégie procédurale", "Stratégie transactionnelle"]
bail_commercial:   ["Assignation en référé-expulsion", "Commandement de payer visant la clause résolutoire", "Négociation d'un protocole d'accord"]
consommation:      ["Action en garantie des vices cachés", "Médiation de la consommation", "Résolution amiable avec le vendeur"]
```

Les trois dossiers ne partagent aucun type de stratégie — la preuve
que le SLAI génère des propositions contextuelles plutôt qu'un
catalogue fixe — et chacune des dix stratégies produites au total
porte sa propre limitation rappelant qu'elle reste une proposition
soumise à validation humaine.
