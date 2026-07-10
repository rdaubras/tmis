# Guide : ajouter un nouveau parser d'ingestion

Le module `tmis.document_intelligence.ingestion` dispatche chaque fichier
au parser qui déclare supporter son content type
(`IngestionRegistry.parse()`). Ajouter un format ne modifie ni le
pipeline, ni les autres parsers.

## Étapes

1. Créer `backend/src/tmis/document_intelligence/ingestion/<nom>_parser.py`
   implémentant `DocumentParserPort` :

   ```python
   from tmis.document_intelligence.schemas.document import IngestedDocument

   class MonParser:
       content_types: tuple[str, ...] = ("application/x-mon-format",)

       def supports(self, content_type: str) -> bool:
           return content_type in self.content_types

       def parse(self, document_id: str, filename: str, raw_bytes: bytes) -> IngestedDocument:
           # Extraire le texte réel ici (ou laisser `text=""` si le texte
           # doit venir d'un moteur OCR — voir docs/16 dans ce cas).
           return IngestedDocument(
               id=document_id,
               filename=filename,
               content_type=self.content_types[0],
               text="...",
               page_count=1,
               raw_bytes=raw_bytes,
           )
   ```

2. L'enregistrer dans `IngestionRegistry` (ajout à la liste par défaut
   dans `registry.py`, ou `registry.register(MonParser())` pour un
   enregistrement dynamique côté cabinet).
3. Si le format ne peut pas encore être réellement lu (cas de `EmlParser`,
   préparé mais non implémenté), lever `NotImplementedError` avec un
   message renvoyant vers la roadmap plutôt que de retourner un résultat
   silencieusement vide.
4. Ajouter des tests suivant le patron de
   `backend/tests/unit/document_intelligence/test_ingestion.py` : un test
   de désignation (`supports`), un test d'extraction réelle avec un
   fichier minimal généré en mémoire (voir `pdf_fixture.py` pour
   l'exemple PDF, ou `python-docx`/`Pillow` pour DOCX/images).

## Ce qui ne change jamais

`DocumentIntelligencePipeline` appelle uniquement
`ingestion_registry.parse(document_id, filename, content_type, raw_bytes)`
— aucun code du pipeline ne connaît le format réel du fichier.
