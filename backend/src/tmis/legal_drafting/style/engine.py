from tmis.legal_drafting.style.schemas import StyleProfile

_CLOSINGS: dict[str, str] = {
    "formal": (
        "Nous vous prions d'agréer, Madame, Monsieur, l'expression de nos "
        "salutations distinguées."
    ),
    "neutral": "Cordialement.",
    "assertive": "Nous restons attentifs à votre réponse dans les meilleurs délais.",
}


class StyleEngine:
    """Implements `StyleEnginePort`: turns a `StyleProfile` into explicit
    prompt instructions for the Paragraph Engine's generation calls, and
    applies a light, deterministic post-processing pass (e.g. the
    closing formula of a `signature` section) — see
    docs/30-guide-moteur-style.md. Actual prose style shaping happens at
    generation time (via the Kernel prompt); this engine never rewrites
    a paragraph's substance, only its framing.
    """

    def prompt_instructions(self, profile: StyleProfile) -> str:
        return (
            f"Ton : {profile.tone}. Niveau de détail : {profile.detail_level}. "
            f"Longueur : {profile.length}. Registre : {profile.register}."
        )

    def apply(self, text: str, profile: StyleProfile) -> str:
        return text

    def closing_formula(self, profile: StyleProfile) -> str:
        return _CLOSINGS.get(profile.tone, _CLOSINGS["neutral"])
