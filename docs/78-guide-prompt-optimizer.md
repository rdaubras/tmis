# Guide — Prompt Optimizer

`tmis.ai_fabric.prompt_optimizer.PromptOptimizer` adapte un prompt au
modèle cible et délègue **entièrement** le versionnage à
`tmis.ai.prompts.PromptRegistry` (Sprint 2) — conformément à l'énoncé
du sprint : "les prompts restent versionnés dans le Prompt Registry".

## Enregistrer un prompt versionné

```python
from tmis.ai_fabric.bootstrap import get_prompt_optimizer

optimizer = get_prompt_optimizer()
optimizer.register(
    "avis-bail-commercial",
    category="drafting",
    template="Rédige un avis juridique sur le bail suivant : {contenu}.",
    variables=("contenu",),
)
```

Chaque appel à `register()` avec le même `prompt_id` crée une nouvelle
version — l'historique complet reste consultable via
`optimizer.history("avis-bail-commercial")`.

## Rendre un prompt

```python
texte = optimizer.render("avis-bail-commercial", contenu="...")
```

## Adapter au modèle cible

```python
from tmis.ai_fabric.bootstrap import get_model_registry

modele = get_model_registry().get("gpt-4-legal")
adapte = optimizer.adapt_for_model(texte, modele)
print(adapte.truncated, adapte.estimated_tokens)
```

`adapt_for_model` tronque le prompt si son estimation de tokens
dépasse `max_context_tokens - 512` (marge réservée à la réponse) du
modèle cible — la troncature se fait par mot entier, jamais au milieu
d'un mot, et `OptimizedPrompt.truncated` indique si une troncature a
eu lieu.

## Étendre l'optimisation

`adapt_for_model` n'implémente aujourd'hui que la troncature par
fenêtre de contexte. Toute nouvelle stratégie d'adaptation (résumé
automatique du prompt, sélection de variante A/B) doit rester dans ce
module et continuer à déléguer le stockage versionné à
`PromptRegistry` plutôt que d'introduire un second mécanisme de
versionnage.
