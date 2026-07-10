# Guide — Rapports

## Une table générique, quatre formats

```python
from tmis.cabinet_os.reports.engine import ReportEngine
from tmis.cabinet_os.reports.schemas import ReportFormat, ReportTable

table = ReportTable(
    title="Chiffre d'affaires", headers=["Client", "Montant"],
    rows=[["Acme", "1000"], ["Beta", "2500.50"]],
)
engine = ReportEngine()
result = engine.generate(table, ReportFormat.PDF)
# result.content (bytes), result.filename, result.media_type
```

N'importe quel moteur du COS (tableaux de bord, analytique,
facturation, temps passé...) peut produire une `ReportTable` sans
connaître le format de sortie — c'est `ReportEngine` qui choisit
l'exporteur.

## Pourquoi deux writers faits main plutôt que deux dépendances

- **PDF** réutilise directement
  `tmis.legal_drafting.export.pdf_writer.build_minimal_pdf` (Sprint 7) :
  TMIS dépend déjà de `pypdf` pour *lire* des PDF, mais rien pour en
  *écrire* — plutôt que d'ajouter `reportlab`/`fpdf`, ce writer minimal
  fait main est réutilisé tel quel.
- **Excel** suit le même principe : `reports/xlsx_writer.py` écrit à la
  main le plus petit paquet OOXML valide (un classeur, une feuille,
  des chaînes en ligne, sans `sharedStrings.xml`), plutôt que d'ajouter
  `openpyxl` pour un export de portée volontairement simple.
- **CSV** et **HTML** n'ont besoin d'aucune dépendance (`csv` de la
  bibliothèque standard, gabarit HTML auto-suffisant).

## Ajouter un format

1. Implémenter `ReportExporterPort.export(table) -> ReportResult`.
2. L'enregistrer dans le dict passé au constructeur de `ReportEngine`,
   ou l'ajouter à `_DEFAULT_EXPORTERS` (`reports/engine.py`) s'il doit
   être disponible partout par défaut.
3. Aucun appelant de `generate()` n'a besoin de changer.

## Où l'API l'expose

`POST /api/v1/cabinet-os/reports/generate` avec
`{"title", "headers", "rows", "report_format"}` — répond avec le
fichier en pièce jointe (`Content-Disposition: attachment`) et le bon
`Content-Type` pour le format demandé.
