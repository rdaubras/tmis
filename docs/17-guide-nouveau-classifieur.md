# Guide : ajouter un nouveau classifieur de documents

`tmis.document_intelligence.classification.KeywordClassifier` est
l'implémentation Sprint 3 de `ClassifierPort` : un classement déterministe
par mots-clés sur les 10 catégories de `DocumentCategory`. Un classifieur
appris (modèle fine-tuné) peut le remplacer sans changer le pipeline.

## Étapes

1. Créer `backend/src/tmis/document_intelligence/classification/<nom>_classifier.py` :

   ```python
   from tmis.document_intelligence.schemas.classification import ClassificationResult

   class MonClassifieur:
       def classify(self, text: str) -> ClassificationResult:
           category, confidence = ...  # inférence réelle ici
           return ClassificationResult(category=category, confidence=confidence)
   ```

2. Le passer à `DocumentIntelligencePipeline(classifier=MonClassifieur())`.
3. Si le classifieur doit reconnaître une nouvelle catégorie non prévue
   par `DocumentCategory` (`schemas/classification.py`), l'ajouter à
   l'énumération d'abord — c'est un contrat partagé par tout le pipeline
   et par le futur module `dashboard`/`case_analysis`.
4. Ajouter des tests suivant `backend/tests/unit/document_intelligence/test_classification.py` :
   au moins un cas par catégorie que le nouveau classifieur doit
   reconnaître, plus un cas de repli vers `DocumentCategory.OTHER`.

## Pourquoi la confiance compte

`ClassificationResult.confidence` est utilisée par le Vérificateur (agents
métier, Sprint 13) pour décider si une classification doit être présentée
comme certaine ou comme une proposition à valider par l'avocat (voir
docs/05-strategie-multi-agents.md) — un nouveau classifieur doit renvoyer
une confiance représentative, pas une valeur arbitraire.
