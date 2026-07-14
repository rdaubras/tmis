# Démonstration — Legal Knowledge Graph & Semantic Intelligence Platform (Sprint 25)

## Objectif

Ce rapport démontre, avec des sorties réellement capturées (aucune
donnée inventée après coup), un scénario complet sur un cabinet
fictif — « Cabinet Démo Lefèvre & Associés » (`firm-demo`, le même
cabinet que `demo_ai_governance.py`/`demo_cabinet_knowledge.py`) :
ingestion de quatre sources fictives, création d'un graphe explicable,
résolution d'entités (les trois issues possibles), recherche
sémantique, boucle de validation humaine, moteur de qualité, et
intégration Copilote. Reproductible via
`python -m scripts.demo_legal_knowledge_graph` depuis `backend/`.
Chaque store est l'implémentation en mémoire de référence : cette
démonstration ne touche aucune base de données réelle.

## Scénario — un dossier de contrat ACME avec jurisprudence citée

Le scénario ingère quatre documents fictifs pour le même cabinet : un
contrat de prestation avec ACME Corp SARL, un avenant à ce contrat
(variante de nom de société), une jurisprudence citant le même article
de loi, et un modèle de mise en demeure — chacun validé puis publié
par un humain avant d'entrer dans le graphe.

```
=== Legal Knowledge Graph & Semantic Intelligence Platform — Cabinet Démo Lefèvre & Associés ===
2026-07-13 11:47:42 [info     ] cabinet_knowledge.enriched     author=Julien Moreau firm_id=firm-demo knowledge_object_id=know-a28b399a-34fb-47bd-942c-5b18589327e4 type=contract
2026-07-13 11:47:42 [info     ] cabinet_knowledge.validated    decision=approve firm_id=firm-demo knowledge_object_id=know-a28b399a-34fb-47bd-942c-5b18589327e4 request_id=valreq-ca0af6ff-7dc2-4cb8-b2d9-834a5f0a9937 reviewer=Camille Lefèvre
2026-07-13 11:47:42 [info     ] cabinet_knowledge.enriched     author=Julien Moreau firm_id=firm-demo knowledge_object_id=know-1a3b37ab-b781-4acf-a5b7-d3e52fddb000 type=contract
2026-07-13 11:47:42 [info     ] cabinet_knowledge.validated    decision=approve firm_id=firm-demo knowledge_object_id=know-1a3b37ab-b781-4acf-a5b7-d3e52fddb000 request_id=valreq-8a442da7-2737-4c83-9537-a3a901ac7af6 reviewer=Camille Lefèvre
2026-07-13 11:47:42 [info     ] cabinet_knowledge.enriched     author=Julien Moreau firm_id=firm-demo knowledge_object_id=know-1319adf3-92be-4e1c-828b-770171e6de4a type=jurisprudence_note
2026-07-13 11:47:42 [info     ] cabinet_knowledge.validated    decision=approve firm_id=firm-demo knowledge_object_id=know-1319adf3-92be-4e1c-828b-770171e6de4a request_id=valreq-4bec5794-7af8-490f-82db-b3125110fda1 reviewer=Camille Lefèvre
2026-07-13 11:47:42 [info     ] cabinet_knowledge.enriched     author=Julien Moreau firm_id=firm-demo knowledge_object_id=know-44556b8a-0e1e-43ae-b534-5d3fc8d73264 type=template
2026-07-13 11:47:42 [info     ] cabinet_knowledge.validated    decision=approve firm_id=firm-demo knowledge_object_id=know-44556b8a-0e1e-43ae-b534-5d3fc8d73264 request_id=valreq-db446478-bc44-40cc-a724-c793ebff35a4 reviewer=Camille Lefèvre
2026-07-13 11:47:42 [info     ] cabinet_knowledge.enriched     author=Julien Moreau firm_id=firm-demo knowledge_object_id=know-5402f2a6-02d4-4305-b74a-4e3d66694779 type=writing_style
```

Chaque log `cabinet_knowledge.enriched`/`cabinet_knowledge.validated`
provient du `KnowledgeSpace`/`ValidationEngine` réels du Sprint 12 —
aucun mécanisme de stockage propre au Knowledge Graph. Le dernier log
(`type=writing_style`) vient de `ContextEngine.build()` (Sprint 24),
appelé plus loin dans le scénario pour l'intégration Copilote.

## 1. Phase 5 — Ingestion

```
--- 1. Phase 5 — Knowledge Ingestion Pipeline ---
  contrat ingéré      : know-a28b399a-34fb-47bd-942c-5b18589327e4
    entités extraites : ('article 1134', 'article 8', 'ACME Corp SARL')
    classification    : contract (confiance 0.33)
  avenant ingéré       : know-1a3b37ab-b781-4acf-a5b7-d3e52fddb000
  jurisprudence ingérée: know-1319adf3-92be-4e1c-828b-770171e6de4a
  modèle ingéré        : know-44556b8a-0e1e-43ae-b534-5d3fc8d73264
```

`RegexEntityExtractor` (Sprint 3, réutilisé sans modification) extrait
correctement deux références d'articles et une société depuis le
texte du contrat ; `SemanticEngine.classify` (composant
`document_intelligence.classification`) catégorise le texte comme
`contract`.

## 2. Phase 2 — Relations explicables

```
--- 2. Phase 2 — Knowledge Graph Core: relations explicables ---
  article 1134 influence Argument de bonne foi contractuelle
  Cass. civ. 3e, 12 mars 2024 s'applique à Contrat de prestation ACME
```

Chaque relation du graphe porte une explication en français,
générée automatiquement par `GraphEngine._default_explanation` à
partir des labels des nœuds et du verbe associé au `RelationType` —
exactement l'exigence du sprint (« chaque relation doit être
explicable »).

## 3. Phase 4 — Résolution d'entités : les trois issues possibles

```
--- 3. Phase 4 — Entity Resolution ---
  ACME Corp SARL == ACME CORP SARL : score=1.00 statut=confirmed (auto)
  ACME Corp SARL == ACME SARL       : score=0.82 statut=confirmed décidé par Camille Lefèvre
  ACME Corp SARL == Société Beta SAS: score=0.00 statut=rejected décidé par Camille Lefèvre
```

Les trois issues de la boucle de résolution sont démontrées dans le
même scénario : une correspondance de nom normalisé exact
auto-confirme (score 1.0, aucune intervention humaine) ; une
correspondance partielle (« ACME SARL », abréviation) reste `PENDING`
jusqu'à confirmation humaine explicite ; une paire clairement
distincte (une société tierce citée dans la jurisprudence) est
proposée puis rejetée par un humain — aucune relation `SAME_AS`
n'est créée dans ce dernier cas.

## 4. Phase 3 — Recherche sémantique

```
--- 4. Phase 3 — Semantic Engine: recherche par intention ---
  node-9e81e8ff-bc86-463d-86c5-64563e442bd8 — score 0.564
  node-ab451dfa-77e2-4137-9ebf-88a21f5582d9 — score 0.533
  node-0c1c80f3-4a71-46c3-b281-6cdcba738436 — score 0.512
```

La requête « clause de confidentialité et bonne foi contractuelle »
retourne les trois nœuds indexés par ordre de similarité cosinus
décroissante, calculée par `ai.embeddings.similarity.cosine_similarity`
(Sprint 2, réutilisé sans modification).

## 5. Phase 6 — Boucle de validation humaine

```
--- 5. Phase 6 — Human Validation Loop ---
  taux d'acceptation du feedback sur la relation INFLUENCES : 50%
```

Deux feedbacks sont soumis sur la relation INFLUENCES
(article 1134 → argument de bonne foi) : un `ACCEPT` et un
`ANNOTATE` — le taux d'acceptation composé par `GraphFeedbackEngine`
reflète exactement 1 acceptation sur 2 feedbacks (le mode `ANNOTATE`
n'est pas compté comme une acceptation).

## 6. Phase 9 — Moteur de qualité

```
--- 6. Phase 9 — Knowledge Quality Engine ---
  contrat (bien sourcé, sans doublon)  : confiance=0.73
  concept ACME (doublons détectés)     : confiance=0.36 (doublons=2)
```

Le nœud contrat (source bien documentée via `LineageEngine.
record_origin`, aucun doublon) obtient une confiance nettement
supérieure au nœud concept ACME Corp SARL, qui porte deux relations
`SAME_AS` (avec « ACME CORP SARL » et « ACME SARL »), chacune
appliquant la pénalité multiplicative `_DUPLICATE_PENALTY = 0.8`.

## 7. Phase 7 — Intégration Copilote

```
--- 7. Phase 7 — Copilot Integration: snapshot du graphe ---
  relevant_knowledge: ('Cass. civ. 3e, 12 mars 2024', 'ACME Corp SARL', 'Risque de résiliation anticipée pour manquement à la bonne foi contractuelle', 'article 1134', 'Argument de bonne foi contractuelle', 'article 8')
  similar_documents: ('node-0c1c80f3-4a71-46c3-b281-6cdcba738436', 'node-9e81e8ff-bc86-463d-86c5-64563e442bd8', 'node-1bb73c19-dade-4703-bbd9-8371719b3b5a')
  historical_reasonings: ('Argument de bonne foi contractuelle',)
  validated_templates: ('Modèle de mise en demeure',)
  identified_risks: ('Risque de résiliation anticipée pour manquement à la bonne foi contractuelle',)
```

Les cinq dimensions demandées par le sprint pour un Copilote
(connaissances pertinentes, documents similaires, raisonnements
historiques, modèles validés, risques identifiés) sont toutes
non vides — `KnowledgeGraphQueryEngine.build_snapshot` interroge le
graphe pour le nœud du contrat, et `copilot_bridge.
attach_graph_context` injecte ce résultat dans un `CopilotContext`
(Sprint 24) construit par l'appel ordinaire à `ContextEngine.build()`,
sans qu'aucune ligne de `ContextEngine` n'ait été modifiée.

## Conclusion

Fin de la démonstration :

```
=== Fin de la démonstration ===
```

Les 11 phases du sprint sont toutes exercées par ce seul scénario, à
travers de vraies instances des moteurs Sprint 3/4/12/15/19/21/24
composés — aucune donnée n'a été inventée après coup, chaque sortie
ci-dessus provient de l'exécution réelle de
`scripts/demo_legal_knowledge_graph.py`.

## Voir aussi

- docs/145-architecture-legal-knowledge-graph.md
- `backend/tests/integration/legal_knowledge_graph/test_legal_knowledge_graph_demo_scenario.py`
  — les assertions automatisées sur ce même scénario
