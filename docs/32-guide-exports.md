# Guide : les exports du Legal Drafting Studio

Trois formats, chacun implémentant `export.ports.ExporterPort`
(`export(document: Document) -> ExportResult`), chacun préservant la
structure du document (titre, sections, paragraphes dans l'ordre) et
ses citations.

## HTML — `export.html_exporter.HtmlExporter`

Un document HTML autonome (`<!doctype html>` inline, aucune dépendance
externe), avec le titre échappé (`html.escape`) contre toute injection,
un rappel explicite que le document est un brouillon en tête de page,
et une note de bas de paragraphe par citation (format
`FootnoteCitationFormatter`).

## DOCX — `export.docx_exporter.DocxExporter`

Utilise `python-docx` (déjà une dépendance TMIS depuis le Sprint 3) :
titre en `Heading 1`, chaque section en `Heading 2`, chaque paragraphe
suivi de ses citations en italique. Le fichier est écrit dans un
`io.BytesIO` puis renvoyé en bytes — jamais sur disque.

## PDF — `export.pdf_writer.build_minimal_pdf`

TMIS dépend déjà de `pypdf` pour *lire* des PDF (Sprint 3), mais aucune
bibliothèque du projet ne sait en *écrire* un et le Sprint 7 ne devait
pas ajouter de dépendance juste pour ce format à portée mock. Plutôt que
d'ajouter `reportlab`/`fpdf`, `pdf_writer.py` construit à la main le
plus petit graphe d'objets PDF valide (Catalog, arbre de Pages, une
page + un flux de contenu par page, police Helvetica partagée) —
suffisant pour que n'importe quel lecteur conforme (dont `pypdf`,
utilisé dans les tests pour relire le contenu généré) l'ouvre et en
extraie le texte.

```python
from tmis.legal_drafting.export.pdf_writer import build_minimal_pdf

content = build_minimal_pdf(["Ligne 1", "Ligne 2"], lines_per_page=45)
```

`export.pdf_exporter.PdfExporter` construit la liste de lignes
(disclaimer, titre, sections, paragraphes, citations en format
`PlainTextCitationFormatter`) puis appelle `build_minimal_pdf`.

## Ajouter un nouveau format

1. Implémenter `ExporterPort` dans un nouveau fichier de `export/`.
2. L'ajouter au dictionnaire `exporters` de
   `DocumentOrchestrator` (ou au paramètre `exporters=` de son
   constructeur pour un déploiement personnalisé) :

   ```python
   DocumentOrchestrator(..., exporters={**default_exporters, ExportFormat.MARKDOWN: MarkdownExporter()})
   ```

3. Étendre `export.schemas.ExportFormat` avec la nouvelle valeur.
4. Aucune autre modification : l'API (`GET .../export?format=...`) et
   l'historique (`DraftHistoryActionType.EXPORTED`) fonctionnent déjà
   pour n'importe quel format enregistré.

## Ce que chaque export garantit

- Le document reste identifiable comme un brouillon (mention explicite
  dans les trois formats).
- L'ordre des sections et des paragraphes est préservé.
- Chaque citation reste rattachée au paragraphe qu'elle justifie.
