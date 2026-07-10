from tmis.legal_drafting.templates.schemas import (
    DocumentTemplate,
    DocumentType,
    SectionRole,
    TemplateSection,
)

# (key, role, title) tuples per document type, in order. `depends_on` is
# derived automatically below: every section depends on the previous one
# whose role is FACTS or LEGAL_DISCUSSION or ARGUMENTS (the sections a
# legal draft actually builds argumentation on top of).
_TEMPLATE_OUTLINES: dict[DocumentType, list[tuple[str, SectionRole, str]]] = {
    DocumentType.CONSULTATION: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("context", SectionRole.CONTEXT, "Contexte de la consultation"),
        ("facts", SectionRole.FACTS, "Exposé des faits"),
        ("legal_discussion", SectionRole.LEGAL_DISCUSSION, "Analyse juridique"),
        ("recommendations", SectionRole.RECOMMENDATIONS, "Recommandations"),
        ("conclusion", SectionRole.CONCLUSION, "Conclusion"),
        ("signature", SectionRole.SIGNATURE, "Signature"),
    ],
    DocumentType.NOTE_INTERNE: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("context", SectionRole.CONTEXT, "Objet de la note"),
        ("facts", SectionRole.FACTS, "Éléments du dossier"),
        ("legal_discussion", SectionRole.LEGAL_DISCUSSION, "Analyse"),
        ("recommendations", SectionRole.RECOMMENDATIONS, "Points d'attention"),
        ("signature", SectionRole.SIGNATURE, "Signature"),
    ],
    DocumentType.COURRIER: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("context", SectionRole.CONTEXT, "Objet"),
        ("arguments", SectionRole.ARGUMENTS, "Développement"),
        ("conclusion", SectionRole.CONCLUSION, "Formule de politesse"),
        ("signature", SectionRole.SIGNATURE, "Signature"),
    ],
    DocumentType.MISE_EN_DEMEURE: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("facts", SectionRole.FACTS, "Rappel des faits"),
        ("legal_discussion", SectionRole.LEGAL_DISCUSSION, "Fondement juridique"),
        ("arguments", SectionRole.ARGUMENTS, "Mise en demeure"),
        ("conclusion", SectionRole.CONCLUSION, "Délai et conséquences"),
        ("signature", SectionRole.SIGNATURE, "Signature"),
    ],
    DocumentType.REQUETE: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("context", SectionRole.CONTEXT, "Objet de la requête"),
        ("facts", SectionRole.FACTS, "Exposé des faits"),
        ("legal_discussion", SectionRole.LEGAL_DISCUSSION, "Discussion"),
        ("arguments", SectionRole.ARGUMENTS, "Moyens"),
        ("conclusion", SectionRole.CONCLUSION, "Par ces motifs"),
        ("signature", SectionRole.SIGNATURE, "Signature"),
    ],
    DocumentType.ASSIGNATION: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("facts", SectionRole.FACTS, "Exposé des faits"),
        ("legal_discussion", SectionRole.LEGAL_DISCUSSION, "Discussion juridique"),
        ("arguments", SectionRole.ARGUMENTS, "Moyens"),
        ("conclusion", SectionRole.CONCLUSION, "Par ces motifs"),
        ("signature", SectionRole.SIGNATURE, "Signature"),
    ],
    DocumentType.CONCLUSIONS: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("facts", SectionRole.FACTS, "Rappel des faits et de la procédure"),
        ("legal_discussion", SectionRole.LEGAL_DISCUSSION, "Discussion"),
        ("arguments", SectionRole.ARGUMENTS, "Moyens et arguments"),
        ("conclusion", SectionRole.CONCLUSION, "Par ces motifs"),
        ("signature", SectionRole.SIGNATURE, "Signature"),
    ],
    DocumentType.MEMOIRE: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("context", SectionRole.CONTEXT, "Objet du mémoire"),
        ("facts", SectionRole.FACTS, "Exposé des faits"),
        ("legal_discussion", SectionRole.LEGAL_DISCUSSION, "Discussion juridique"),
        ("arguments", SectionRole.ARGUMENTS, "Argumentation"),
        ("recommendations", SectionRole.RECOMMENDATIONS, "Points de vigilance"),
        ("conclusion", SectionRole.CONCLUSION, "Conclusion"),
        ("signature", SectionRole.SIGNATURE, "Signature"),
    ],
    DocumentType.SYNTHESE: [
        ("header", SectionRole.HEADER, "En-tête"),
        ("context", SectionRole.CONTEXT, "Contexte"),
        ("facts", SectionRole.FACTS, "Faits marquants"),
        ("legal_discussion", SectionRole.LEGAL_DISCUSSION, "Analyse"),
        ("conclusion", SectionRole.CONCLUSION, "Synthèse"),
    ],
}

_ARGUMENTATIVE_ROLES = {SectionRole.FACTS, SectionRole.LEGAL_DISCUSSION, SectionRole.ARGUMENTS}


def _build_template(document_type: DocumentType, version: int = 1) -> DocumentTemplate:
    outline = _TEMPLATE_OUTLINES[document_type]
    sections: list[TemplateSection] = []
    previous_argumentative_key: str | None = None
    for order, (key, role, title) in enumerate(outline):
        depends_on = (previous_argumentative_key,) if previous_argumentative_key else ()
        sections.append(
            TemplateSection(key=key, role=role, title=title, order=order, depends_on=depends_on)
        )
        if role in _ARGUMENTATIVE_ROLES:
            previous_argumentative_key = key
    return DocumentTemplate(
        id=f"{document_type.value}:v{version}",
        document_type=document_type,
        version=version,
        name=document_type.value.replace("_", " ").capitalize(),
        sections=tuple(sections),
        variables=("client_name", "case_reference", "firm_name"),
        rules=("Toute affirmation doit être reliée à une source traçable.",),
        controls=("references_present", "no_incomplete_required_section"),
    )


class TemplateRegistry:
    """Implements `TemplateRegistryPort`: an in-memory catalog seeded with
    the nine templates the Sprint 7 prompt asks for, each versioned (see
    docs/29-guide-nouveau-modele-documentaire.md). Registering a new
    version never removes the previous one — `list_versions` always
    returns the full history, `get_latest` the highest version number.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, DocumentTemplate] = {}
        self._by_type: dict[DocumentType, list[DocumentTemplate]] = {}
        for document_type in DocumentType:
            self.register(_build_template(document_type))

    def register(self, template: DocumentTemplate) -> None:
        self._by_id[template.id] = template
        self._by_type.setdefault(template.document_type, []).append(template)

    def get(self, template_id: str) -> DocumentTemplate | None:
        return self._by_id.get(template_id)

    def list_versions(self, document_type: DocumentType) -> list[DocumentTemplate]:
        return list(self._by_type.get(document_type, []))

    def get_latest(self, document_type: DocumentType) -> DocumentTemplate:
        versions = self._by_type.get(document_type, [])
        if not versions:
            raise ValueError(f"No template registered for {document_type!r}")
        return max(versions, key=lambda t: t.version)
