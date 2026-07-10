# Guide : ajouter un nouveau moteur OCR

Le module `tmis.document_intelligence.ocr` sépare la sélection du moteur
(`OcrEngineRegistry`) de son implémentation (`OcrEnginePort`). Sprint 3
ne connecte aucun moteur d'OCR réel : `PassthroughOcrEngine` réutilise le
texte déjà extrait par un parser (PDF/DOCX/TXT), `NullOcrEngine` est un
placeholder explicite pour les images scannées.

## Étapes pour brancher un vrai moteur d'image-vers-texte

1. Créer `backend/src/tmis/document_intelligence/ocr/engines/<nom>_engine.py` :

   ```python
   from tmis.document_intelligence.schemas.document import IngestedDocument
   from tmis.document_intelligence.schemas.ocr import OcrResult

   class MonMoteurOcr:
       engine_name = "mon_moteur"

       def extract_text(self, document: IngestedDocument) -> OcrResult:
           # `document.raw_bytes` porte les octets originaux (l'image),
           # utile puisque `document.text` est vide pour un scan.
           text, confidence = ...  # appel réel au moteur ici
           return OcrResult(text=text, confidence=confidence, engine=self.engine_name)
   ```

2. Le passer à `OcrEngineRegistry(image_engine=MonMoteurOcr())`, ou à
   `DocumentIntelligencePipeline(ocr_registry=OcrEngineRegistry(image_engine=MonMoteurOcr()))`.
   Aucune autre étape du pipeline ne change.
3. Ajouter des tests suivant `backend/tests/unit/document_intelligence/test_ocr.py` :
   au minimum un test vérifiant que `extract_text()` renvoie un texte
   non vide avec une confiance cohérente pour une image connue.

## Rotation et détection de langue

`RotationDetectorPort` et `LanguageDetectorPort` suivent le même principe :
`NullRotationDetector` (toujours 0°) et `HeuristicLanguageDetector`
(fréquence de mots vides fr/en) sont remplaçables sans toucher au
pipeline. Un détecteur de rotation réel (analyse d'image) s'ajoute de la
même façon qu'un moteur OCR : une nouvelle classe implémentant
`RotationDetectorPort`, injectée dans le pipeline.
