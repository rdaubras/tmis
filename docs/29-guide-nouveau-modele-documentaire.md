# Guide : créer un nouveau modèle documentaire

Chaque modèle (`DocumentTemplate`) décrit la structure d'un type de
document sans jamais toucher au reste du Legal Drafting Studio : le
`DocumentBuilder` et le `ParagraphEngine` savent déjà générer n'importe
quelle section pourvu qu'elle porte un `SectionRole` connu.

## Étapes

1. Ajouter le nouveau type à `templates.schemas.DocumentType` (ou, pour
   un modèle personnalisé d'un cabinet, garder le type existant le plus
   proche et changer seulement `name`/`id`).
2. Décrire sa structure comme une liste de `(key, role, title)` dans
   `templates.registry._TEMPLATE_OUTLINES` — ou construire directement
   un `DocumentTemplate` si le modèle vit hors du registre par défaut :

   ```python
   from tmis.legal_drafting.templates.schemas import (
       DocumentTemplate, DocumentType, SectionRole, TemplateSection,
   )

   mon_modele = DocumentTemplate(
       id="consultation:v2",
       document_type=DocumentType.CONSULTATION,
       version=2,
       name="Consultation (variante cabinet X)",
       sections=(
           TemplateSection(key="header", role=SectionRole.HEADER, title="En-tête", order=0),
           TemplateSection(
               key="facts", role=SectionRole.FACTS, title="Faits", order=1,
           ),
           TemplateSection(
               key="legal_discussion", role=SectionRole.LEGAL_DISCUSSION,
               title="Analyse", order=2, depends_on=("facts",),
           ),
           TemplateSection(key="signature", role=SectionRole.SIGNATURE, title="Signature", order=3),
       ),
       variables=("client_name", "case_reference", "firm_name"),
       rules=("Toute affirmation doit être reliée à une source traçable.",),
       controls=("references_present",),
   )
   ```

3. Enregistrer le modèle : `template_registry.register(mon_modele)`.
   `register()` n'écrase jamais une version existante — `get_latest()`
   choisit toujours le numéro de version le plus élevé, `list_versions()`
   garde l'historique complet.
4. Si une section utilise un rôle qui n'existe pas encore
   (`SectionRole`), l'étendre, puis ajouter la branche correspondante
   dans `paragraphs.HeuristicParagraphEngine._generate_content()` — sans
   quoi elle tombera dans la génération générique fondée sur la
   synthèse du raisonnement.
5. Ajouter un test vérifiant l'ordre des sections et les dépendances
   (voir `backend/tests/unit/legal_drafting/test_drafting_templates.py`).

## Règle à respecter systématiquement

`depends_on` doit toujours référencer une section qui apparaît **avant**
dans l'ordre du modèle (le `DocumentBuilder` construit dans l'ordre
`TemplateSection.order`, il ne résout pas un graphe de dépendances
arbitraire). C'est une information pour l'instant descriptive, mais un
futur planificateur s'appuiera dessus pour valider ou paralléliser
l'ordre de construction.
