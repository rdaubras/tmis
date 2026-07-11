# Guide du Consensus Engine (Sprint 11)

## Rôle

`ConsensusEngine.build_consensus(topic, positions)` compare les
réponses de plusieurs agents sur une même question, identifie les
divergences, produit un consensus argumenté et signale les désaccords
persistants — exactement ce que le sprint demande, sans jamais
générer de texte nouveau : le "consensus" retenu est toujours l'une
des positions soumises, jamais une réécriture.

## Méthode de comparaison

`ConsensusEngine` utilise une similarité de Jaccard sur les ensembles
de mots (`_similarity`) — une heuristique légère, sans dépendance ni
appel à un modèle d'embedding. Pour chaque position, la similarité
moyenne avec toutes les autres est calculée
(`agreement_ratio` = moyenne globale) ; la position retenue comme
"consensus" est celle dont la similarité moyenne (puis la confiance
déclarée, en cas d'égalité) est la plus élevée.

```python
result = consensus_engine.build_consensus(
    "durée du préavis",
    [
        AgentPosition("agent-legal-researcher", "...", ConfidenceLevel.HIGH),
        AgentPosition("agent-jurisprudence-expert", "...", ConfidenceLevel.MEDIUM),
    ],
)
result.agreement_ratio         # 0.0 à 1.0
result.consensus_text          # la position retenue
result.disagreements           # ids des agents dont la position diverge nettement
```

Un agent dont la similarité moyenne tombe sous 0,4 (`_AGREEMENT_THRESHOLD`)
est signalé dans `disagreements` — un désaccord persistant.

## Negotiation Engine

`NegotiationEngine.negotiate(topic, positions)` s'appuie directement
sur `ConsensusEngine` : si aucun désaccord persistant n'est détecté,
la négociation est trivialement résolue (`resolved=True`, aucun
round). Sinon, un round est enregistré pour chaque agent en
désaccord (`NegotiationRound`), et l'issue est marquée non résolue —
soumise à validation humaine.

**Limite assumée ce sprint** : cette implémentation est structurelle —
elle enregistre les positions divergentes, elle ne fait pas dialoguer
les agents entre eux pour tenter une convergence réelle (qui
nécessiterait un second appel `TMISKernel.complete()` par agent en
désaccord, informé des autres positions). C'est l'extension naturelle
prévue pour un sprint ultérieur ; le point d'insertion (`negotiate()`)
est déjà en place.

## Context Engine

`ContextEngine` (voir aussi docs/58-architecture-ai-team-platform.md)
partage la même préoccupation de traçabilité : `trace_for_mission`
conserve, pour chaque agent ayant reçu du contexte, la liste exacte
des clés transmises et une estimation du nombre de tokens — utile pour
auditer *pourquoi* deux agents en désaccord n'avaient peut-être pas
reçu le même contexte de départ.
