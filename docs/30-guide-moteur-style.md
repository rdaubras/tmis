# Guide : le Style Engine du Legal Drafting Studio

`style.StyleProfile` capture la charte rédactionnelle d'un cabinet :

```python
@dataclass(frozen=True, slots=True)
class StyleProfile:
    id: str
    firm_name: str
    tone: str = "formal"          # formal | neutral | assertive
    detail_level: str = "standard"  # concise | standard | detailed
    length: str = "standard"        # short | standard | long
    register: str = "soutenu"       # libre : "soutenu", "direct", ...
```

## Où le style agit

1. **À la génération** : `StyleEngine.prompt_instructions(profile)`
   traduit le profil en instructions explicites, injectées dans chaque
   prompt du `ParagraphEngine` — c'est le principal levier : un ton
   `assertive` et une longueur `short` changent réellement ce que le
   modèle produit.
2. **En sortie déterministe** : `StyleEngine.closing_formula(profile)`
   fournit la formule de politesse de la section `signature`, sans
   appel modèle — trois formules par défaut (`formal`, `neutral`,
   `assertive`), extensibles.
3. **Post-traitement** : `StyleEngine.apply(text, profile)` est le point
   d'extension pour une normalisation légère (espacement, ponctuation)
   qui ne changerait jamais le fond du paragraphe — volontairement une
   passe transparente aujourd'hui.

## Enregistrer la charte d'un nouveau cabinet

```python
from tmis.legal_drafting.style.schemas import StyleProfile

style_registry.register(
    StyleProfile(
        id="cabinet-x",
        firm_name="Cabinet X",
        tone="assertive",
        detail_level="detailed",
        length="long",
        register="direct",
    )
)
```

Le profil est ensuite sélectionné par son `id` lors de la création d'un
brouillon (`style_profile_id="cabinet-x"` dans la requête
`POST /legal-drafting/drafts`) — voir docs/28-legal-drafting.md pour le
workflow complet. `StyleProfileRegistry.get()` retombe sur le profil
`"default"` si l'id demandé est inconnu, jamais sur une erreur.

## Ajouter un nouveau moteur de style

Toute classe implémentant `StyleEnginePort` (`prompt_instructions`,
`apply`, `closing_formula`) peut remplacer `StyleEngine` derrière le
port, injectée dans `DocumentOrchestrator(style_engine=...)` — par
exemple pour brancher un vrai contrôle de ton via
`TMISKernel.complete()` plutôt qu'une simple table de formules.
