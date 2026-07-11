# Démonstration — Chaîne d'explicabilité complète (Sprint 15)

Généré par `backend/scripts/demo_ai_governance.py` (`python -m
scripts.demo_ai_governance`), sur le même cabinet fictif que la
démonstration du Sprint 12 (`firm-demo` / "Cabinet Démo Lefèvre &
Associés"), composant uniquement `tmis.ai_governance`. Aucune écriture
en base réelle — tous les stores sont les implémentations en mémoire.

## Dossier fictif

**Question posée** : *Le bailleur peut-il résilier le bail commercial
pour défaut de paiement des loyers ?*

Ce dossier traverse les 15 étapes de la plateforme de gouvernance,
répondant à chacune des questions posées par la Vision du sprint.

## Sortie de la démonstration

```
=== AI Governance & Explainability Platform — démonstration pour Cabinet Démo Lefèvre & Associés ===
Dossier fictif : prod-bail-commercial-2026-01 — Le bailleur peut-il résilier le bail commercial pour défaut de paiement des loyers ?

--- 1. Reasoning Chain — chaîne logique complète ---
  [question] Le bailleur peut-il résilier le bail commercial pour défaut de paiement des loyers ?
  [analyse] Analyse de la clause résolutoire et du commandement de payer.
  [recherche] Recherche jurisprudentielle sur l'effet de la clause résolutoire.
  [arguments] La clause résolutoire expresse est valable et son jeu automatique.
  [contre_arguments] Le preneur pourrait invoquer un délai de grâce judiciaire.
  [consensus] Les deux agents convergent : résiliation fondée sous réserve d'un délai de grâce.
  [validation] Soumis à validation hiérarchique.
  [brouillon] Le bailleur est fondé à demander la résiliation du bail commercial sur le fondement de la clause résolutoire expresse prévue à l'article 12 du contrat, dès lors que le commandement de payer visant cette clause est resté sans effet pendant plus d'un mois. Art. 1103 du Code civil impose par ailleurs la force obligatoire des conventions légalement formées.

--- 2. Provenance — chaque affirmation reliée à sa source ---
  [sentence] "clause résolutoire expresse prévue à l'article 12 du contrat" -> Contrat de bail commercial, art. 12
  [sentence] 'Art. 1103 du Code civil impose par ailleurs la force obligatoire' -> Code civil, art. 1103

--- 3. Traceability — chaîne complète, identifiants uniques ---
  [user] Julien Moreau — utilisateur Julien Moreau
  [case] dossier-bail-2026-01 — dossier dossier-bail-2026-01
  [model_version] gpt-4-legal@2024-08 — modèle gpt-4-legal version 2024-08
  [model_version] claude-legal@4.5 — modèle claude-legal version 4.5
  [prompt] prompt-analyse-bail-v3 — prompt prompt-analyse-bail-v3
  [intermediate_response] resp-1 — Synthèse de la clause résolutoire produite.

--- 4. Decision Records — registre des décisions ---
  décision enregistrée : Engager la procédure sur le fondement de la clause résolutoire expresse.

--- 5. Confidence Engine — score décomposé ---
  score global : 0.69 — qualité des sources 0.85, cohérence du raisonnement 0.90, validation humaine 0.00, consensus multi-agents 0.80, stabilité des modèles 0.90.

--- 6. Risk Engine — risques classés par gravité ---
  [medium] no_human_validation — Cette production n'a pas encore été relue ni validée par un utilisateur humain.

--- 7. Bias / Hallucination / Ethics — détection explicable ---
  biais détectés : 0
  alertes d'hallucination : 0
  alertes déontologiques : 0

--- 8. Policy Engine — politiques du cabinet ---
  export autorisé avant validation : False
    - validation humaine obligatoire avant export : Toute réponse concernant une résiliation doit être validée avant envoi au client.
    - relecture obligatoire pour ce type de dossier (bail_commercial) : Les dossiers de baux commerciaux nécessitent une relecture associé.

--- 9. Human Validation — validation hiérarchique ---
  statut de validation : approved

--- 10. AI Audit — journal spécialisé ---
  1 entrée(s) d'audit enregistrée(s)

--- 11. Compliance — vérification finale avant export ---
  conforme après validation : True

--- 12. Quality Engine — score global de gouvernance ---
  score global de gouvernance : 0.90

--- 13. Explainability Report — lisible par un avocat ---
  résumé : Le bailleur peut engager la résiliation du bail commercial sur la base de la clause résolutoire expresse, sous réserve d'un possible délai de grâce judiciaire.

--- 14. Reporting — rapport d'explicabilité généré ---
  [Résumé] Le bailleur peut engager la résiliation du bail commercial sur la base de la cla
  [Étapes suivies] Le bailleur peut-il résilier le bail commercial pour défaut de paiement des loye
  [Agents impliqués] Analyste documentaire, Chercheur juridique, Rédacteur
  [Modèles utilisés] gpt-4-legal, claude-legal
  [Références juridiques] Code civil, art. 1103
Contrat de bail commercial, art. 12
  [Documents consultés] Contrat de bail commercial
Commandement de payer
  [Éléments ignorés] Aucun

--- 15. Overview — toutes les informations consultables en une lecture ---
  étapes de raisonnement : 8
  éléments de provenance : 2
  entrées de traçabilité : 6
  décisions enregistrées : 1
  demandes de validation : 1
  risques identifiés : 1
  confiance : 0.69

=== Fin de la démonstration ===
```

## Lecture

Cette démonstration illustre le mécanisme central du sprint : le
**Policy Engine bloque l'export tant que la validation humaine
hiérarchique n'a pas eu lieu** (étape 8, `export autorisé avant
validation : False`), puis, une fois la validation associé → partner
obtenue (étape 9), la même vérification de conformité repasse
`conforme après validation : True` (étape 11) — la production n'est
donc jamais "considérée comme définitive" avant d'avoir satisfait les
politiques configurées par le cabinet, exactement comme l'exige la
contrainte du sprint.

L'étape 15 (`Overview`) répond, en une seule lecture, à chacune des
neuf questions posées par la Vision du sprint : pourquoi cette
réponse (résumé de l'étape 13), quels faits (chaîne de raisonnement),
quelles sources (provenance), quels agents (traçabilité et rapport
d'explicabilité), quels modèles (traçabilité), quelles hypothèses
(decision record), quels risques (risk engine), quel niveau de
confiance (confidence engine), quelles validations humaines (human
validation).
