# Guide : ajouter un nouveau connecteur au Legal Research Engine

Le LRE ne possède **pas** son propre gestionnaire de connecteurs : il
étend le `ConnectorManager` du AI Kernel (Sprint 2, voir
docs/13-guides-extension.md § 3) avec ses propres connecteurs
(`internal_documentation`, `private_database`), enregistrés sur la
même instance que `codes`/`jurisprudence`/`doctrine`. Ajouter un
connecteur au LRE suit donc exactement le même patron que dans le
Kernel — ce guide ne fait qu'en préciser le point d'enregistrement côté
LRE.

## Étapes

1. Créer `backend/src/tmis/legal_research/connectors/<nom>_connector.py`,
   implémentant `tmis.ai.connectors.ports.ConnectorPort` :

   ```python
   from tmis.ai.connectors.exceptions import ConnectorAuthenticationError
   from tmis.ai.schemas.connector import ConnectorDocument

   class MonConnecteurLRE:
       connector_name = "mon_connecteur_lre"

       def __init__(self, api_key: str | None = "demo-key") -> None:
           self._api_key = api_key

       async def search(self, query, filters=None) -> list[ConnectorDocument]:
           if not self._api_key:
               raise ConnectorAuthenticationError(self.connector_name, "missing API key")
           ...  # fixture en mémoire tant qu'aucune source réelle n'est branchée

       async def fetch(self, document_id: str) -> ConnectorDocument | None:
           ...
   ```

2. L'ajouter dans `connectors/registration.py::register_legal_research_connectors`,
   qui l'enregistre sur le `ConnectorManager` **partagé** du Kernel :

   ```python
   connector_manager.register("mon_connecteur_lre", MonConnecteurLRE())
   ```

3. Décrire son autorité de source dans `sources/registry.py`
   (`SourceRegistry`), pour que le Ranking Engine sache le pondérer :

   ```python
   SourceDescriptor(
       connector_name="mon_connecteur_lre",
       category=SourceCategory.DOCTRINE,  # ou la catégorie appropriée
       display_name="Mon connecteur",
       authority_score=0.5,
   )
   ```

   Un connecteur non décrit reste utilisable : `SourceRegistry.authority_score()`
   retombe sur un score neutre plutôt que d'échouer.

4. Aucune autre modification n'est nécessaire : `HybridResearchSearch`
   interroge tous les connecteurs activés via `TMISKernel.search_connectors()`
   (ou seulement ceux passés explicitement dans `connector_names`) —
   ajouter un connecteur ne touche ni `ResearchOrchestrator`, ni
   `SourceNormalizer`, ni `ConfigurableRanker`.
5. Ajouter les tests (recherche, `fetch`, enregistrement auprès du
   manager) en suivant le patron de
   `backend/tests/unit/legal_research/test_research_connectors.py`.

## Ce qui reste vrai quelle que soit la source

Le Sprint 5 ne connecte que des fixtures en mémoire
(`InMemoryDocumentation`/`PrivateDatabase`) pour valider l'architecture
sans dépendance externe. Le jour où une vraie source légale/
jurisprudentielle/documentaire est branchée, elle prend la forme d'un
nouveau connecteur suivant exactement ce guide — le reste du LRE
(normalisation, ranking, citations, cache) n'a besoin d'aucun
changement.
