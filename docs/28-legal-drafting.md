# Legal Drafting Studio (LDS) — architecture (Sprint 7)

## Rôle du moteur

Le Legal Drafting Studio (`backend/src/tmis/legal_drafting/`) transforme
ce que les quatre moteurs précédents ont produit — le Document
Intelligence Engine (Sprint 3), le Case Intelligence Engine (Sprint 4),
le Legal Research Engine (Sprint 5) et le Legal Reasoning Engine
(Sprint 6) — en un projet de document prêt à être relu, modifié et
validé par l'avocat.

**Il ne rédige jamais seul.** Tout document produit est, et reste, un
brouillon : `Document.is_draft` est une propriété qui renvoie toujours
`True`, sans aucun code capable de la modifier. Le workflow interne
(`DraftWorkflowStatus`) suit une relecture — générée, en relecture,
approuvée par l'avocat, rejetée — mais même `LAWYER_APPROVED` ne
signifie qu'une validation interne du contenu par l'avocat dans TMIS,
jamais un acte juridique.

Comme les Sprints 2-6, le seul appel à un fournisseur de modèle de tout
le moteur passe par `TMISKernel.complete()` — un unique point d'entrée,
dans le Paragraph Engine.

## Vue d'ensemble des modules

```mermaid
flowchart TB
    subgraph Upstream["Moteurs consommés (Sprints 4-6)"]
        CIE["CaseIntelligenceWorkflow (Sprint 4)"]
        LRE["ResearchOrchestrator (Sprint 5)"]
        LRE2["ReasoningOrchestrator (Sprint 6)"]
    end
    subgraph Leaf["Modules de base"]
        TPL[templates]
        STYLE[style]
        REF[references]
        CIT[citations] --> REF
        PARA[paragraphs] --> STYLE
        SEC[sections] --> PARA
        REV[review]
        VAL[validation]
        VERS[versioning]
        HIST[history]
        EXP[export] --> CIT
        EVAL[evaluation]
    end
    subgraph Root["Racine de composition"]
        DOC[documents.DocumentOrchestrator]
    end

    CIE -.narrow port DraftingCasePort.-> DOC
    LRE -.narrow port DraftingResearchPort.-> DOC
    LRE2 -.narrow port DraftingReasoningPort.-> DOC
    TPL --> DOC
    Leaf --> DOC
    DOC --> AIKERNEL["TMISKernel.complete() — via paragraphs uniquement"]
```

`documents/ports.py` définit trois ports étroits —
`DraftingCasePort`, `DraftingResearchPort`, `DraftingReasoningPort` —
mêmes principes que `tmis.legal_reasoning.reasoner.ports` (Sprint 6) :
le LDS ne réimplémente jamais l'analyse de dossier, la recherche
documentaire ou le raisonnement juridique, il compose ce qui existe
déjà via de fins adaptateurs (`documents/adapters.py`).

## De la demande au brouillon publié

```mermaid
sequenceDiagram
    actor Avocat
    participant API as API REST
    participant Doc as DocumentOrchestrator
    participant CIE as CaseIntelligenceWorkflow
    participant LRE as ResearchOrchestrator
    participant LRE2 as ReasoningOrchestrator
    participant Build as DocumentBuilder
    participant Para as ParagraphEngine
    participant Ref as ReferenceResolver
    participant Rev as ReviewEngine

    Avocat->>API: POST /legal-drafting/drafts {document_type, case_id, question}
    API->>Doc: create_draft(...)
    Doc->>CIE: get_profile(case_id)
    Doc->>LRE: search(question, case_id)
    Doc->>LRE2: reason(question, case_id) [ou get_session(id)]
    Doc->>Doc: sélection du modèle documentaire (TemplateRegistry)
    Doc->>Build: build_sections(template.sections, contexte)
    Build->>Para: generate(section, contexte) — un appel Kernel par section
    Doc->>Ref: resolve(paragraphe, contexte) pour chaque paragraphe
    Doc->>Doc: CitationEngine.build_for_paragraph(...)
    Doc->>Rev: review(sections, template, reasoning_session)
    Doc->>Doc: création du Document (statut UNDER_REVIEW)
    Doc-->>API: Document (brouillon, mis à disposition pour relecture)
    API-->>Avocat: brouillon + citations + constats de relecture
```

`DocumentOrchestrator` (`documents/orchestrator.py`) est la racine de
composition : chaque dépendance est injectée derrière un port avec une
implémentation par défaut, sur le même principe que
`ReasoningOrchestrator`/`ResearchOrchestrator` (Sprints 5-6). L'étape
"Preuves" du Legal Reasoning Engine n'est pas rejouée : le LDS lit
directement `ReasoningSession.evidence_links` déjà calculés.

## Template Engine : neuf modèles, tous versionnés

`templates.TemplateRegistry` catalogue les neuf types de documents
demandés (`consultation`, `note_interne`, `courrier`,
`mise_en_demeure`, `requete`, `assignation`, `conclusions`, `memoire`,
`synthese`), chacun sous la forme d'un `DocumentTemplate` immuable :
structure (`sections` ordonnées avec dépendances), `variables`,
`rules`, `controls`. Une nouvelle version s'ajoute sans jamais
remplacer l'ancienne (`register()` ne fait qu'ajouter) — voir
docs/29-guide-nouveau-modele-documentaire.md.

Les sections partagent un ensemble de rôles génériques
(`SectionRole` : `HEADER`, `CONTEXT`, `FACTS`, `LEGAL_DISCUSSION`,
`ARGUMENTS`, `RECOMMENDATIONS`, `CONCLUSION`, `SIGNATURE`), pour que le
Paragraph Engine sache générer un contenu sans connaître le type de
document — seule la table `_TEMPLATE_OUTLINES` du `TemplateRegistry`
varie d'un modèle à l'autre.

## Document Builder : sections indépendamment régénérables

`sections.DocumentBuilder` assemble les sections dans l'ordre du
modèle. `depends_on` est informatif à ce stade (l'ordre du modèle
respecte déjà toutes les dépendances) — il permettra à un futur
planificateur de paralléliser des sections indépendantes sans changer
`DocumentBuilder`. Régénérer une section (`regenerate_section`) ne
reconstruit qu'elle : `DocumentOrchestrator` conserve ensuite l'id de
la section et, position par position, l'id de chaque paragraphe déjà
présent, pour que le versioning voie une **modification** plutôt qu'une
suppression suivie d'un ajout.

## Paragraph Engine : traçabilité stricte

`paragraphs.HeuristicParagraphEngine` génère un paragraphe par rôle de
section. `header` et `signature` sont du texte déterministe (aucun
appel Kernel) ; tous les autres rôles passent par
`TMISKernel.complete()` — le seul point d'appel LLM de tout le moteur.
Chaque paragraphe ne déclare comme traçabilité (`fact_ids`,
`reference_ids`, `evidence_ids`, `hypothesis_ids`) que ce qui a
réellement nourri son prompt : une section "faits" ne cite que les
faits effectivement inclus, une section "discussion juridique" que les
hypothèses et références effectivement citées. `regenerate_one()`
régénère un paragraphe isolément en conservant son id et son ordre.

## Citation Engine et Reference Resolver

`references.HeuristicReferenceResolver` transforme les ids bruts d'un
paragraphe en `ReferenceLink` lisibles, en consultant directement les
données des moteurs amont (faits, résultats de recherche, preuves et
hypothèses du raisonnement) — jamais de recalcul.
`citations.CitationEngine` transforme ensuite ces `ReferenceLink` en
`DraftCitation` ancrées au document, à la section et au paragraphe
précis, avec plusieurs formats de sortie (`PlainTextCitationFormatter`,
`FootnoteCitationFormatter`).

## Style Engine

`style.StyleEngine` traduit un `StyleProfile` (ton, niveau de détail,
longueur, registre) en instructions explicites pour le prompt du
Paragraph Engine, et fournit la formule de politesse déterministe de la
section signature. `style.StyleProfileRegistry` permet à chaque cabinet
d'enregistrer sa propre charte — voir docs/30-guide-moteur-style.md.

## Review Engine : ne corrige jamais

`review.HeuristicReviewEngine` détecte cinq catégories de problèmes
(répétitions, contradictions — en réutilisant les `Conflict` du
Sprint 6 —, sections incomplètes, références absentes, paragraphes non
justifiés) et se contente de les **signaler** : aucune correction
automatique n'est appliquée sans validation humaine.

## Human In The Loop

`validation.HumanInTheLoopService` enregistre chaque décision
(approuver / rejeter / commenter) sans jamais en écraser une
précédente, et sans jamais toucher à `Document.is_draft`. Le workflow
n'est donc jamais "terminé" au sens juridique : il attend toujours
l'avocat.

## Versioning et historique

`versioning.InMemoryVersioningService` conserve un instantané
(deep-copy) à chaque création ou régénération — voir
docs/31-guide-versioning.md pour la comparaison et la restauration.
`history.InMemoryDraftHistory` journalise séparément **toute** action
(création, régénération de section/paragraphe, relecture, validation,
restauration, export), humaine ou automatique — l'historique est un
journal d'audit, le versioning un mécanisme de restauration de
contenu.

## Persistance & isolation multi-tenant (tranche `cases -> drafting`)

Le Sprint 7 stockait tout en mémoire (voir "Portée du Sprint 7"
ci-dessous) ; la tranche verticale `cases -> drafting` fait du parcours
`login -> dossier -> brouillon` le premier **de bout en bout** :
persistant (survit à un redémarrage), isolé par cabinet, et consommé par
un vrai frontend. `case` (`tmis.domain.case`, `SqlAlchemyCaseRepository`)
était déjà la référence ; cette tranche généralise le pattern à
`legal_drafting.documents` sans le déployer sur les autres modules
(prochaine étape).

**ADR-SLICE-01 — Une seule table de drafts, avec `firm_id`.**
`drafting_documents` (JSON payload conservé) gagne une colonne `firm_id`
indexée, jamais dans le payload (migration `0008`). Point d'attention
réconcilié : la migration `0005_document_draft` porte un nom trompeur —
son `upgrade()` créait déjà `drafting_documents` (pas une table
`document_draft` séparée), donc il n'y avait rien à `drop_table` ; `0008`
documente cette lecture plutôt que de fabriquer une suppression de table
inexistante. Les versions de draft (cœur du module, voir "Versioning et
historique") ont elles aussi leur table, `drafting_document_versions`
(migration `0009`), scopée `firm_id` de la même façon.

**ADR-SLICE-02 — Collaborateurs sans état en singleton, stores injectés
par requête.** `legal_drafting.bootstrap.get_document_orchestrator`
n'est plus un singleton `lru_cache` porteur d'un store partagé (grep de
contrôle : aucun `lru_cache` ne doit envelopper un orchestrateur qui
détient un store). Restent en singleton cachés uniquement les
collaborateurs **sans état** : le kernel et les moteurs amont (Sprints
4-6, inchangés), `TemplateRegistry`, `StyleProfileRegistry`,
`StyleEngine` (données/formatage fixes, indépendants du cabinet). Le
`SQLAlchemyDraftDocumentStore` et le `SQLAlchemyVersioningService` sont
construits à chaque requête, adossés à la `Session` de la requête
(`Depends(get_db_session)`) et scopés par `principal.firm_id`
(`Depends(get_current_firm_id)`) — chaque méthode qu'ils exposent passe
par `core.tenancy.scoped_query`, exactement comme
`SqlAlchemyCaseRepository`. `firm_id` est fixé à la construction (pas un
paramètre de méthode) : le port `DocumentStorePort`/`VersioningPort`
garde sa signature d'origine, et `DocumentOrchestrator` n'a besoin
d'aucun changement d'API publique — signal que le pattern reste aussi
lisible que la version `case`.

**Dette technique assumée (documentée, pas silencieuse) :** l'historique
(`InMemoryDraftHistory`), la validation (`HumanInTheLoopService`), le
Review Engine et le Style Engine restent en mémoire et **partagés entre
cabinets** (toujours des singletons de processus). Les construire par
requête sans les persister aurait fait disparaître leur état entre deux
requêtes — une régression, pas un progrès — donc ils restent des
singletons jusqu'à leur propre passage en persistance. C'est un choix
explicite de périmètre (voir la tâche source de ce sprint), pas un oubli.

**ADR-SLICE-03 — Le token est la seule source du `firm_id`, aussi côté
draft.** `create_draft` dérive `firm_id` de `get_current_firm_id` puis,
si `case_id` est fourni, vérifie que ce dossier appartient au cabinet
appelant via `SqlAlchemyCaseRepository.get_by_id(case_uuid, firm_id)` —
sinon `404` (jamais un draft rattaché au dossier d'un autre cabinet).
Point de vigilance résolu explicitement : `Document.case_id` est une
chaîne (partagée avec l'identifiant, non lié au cabinet, du
`CaseProfile` de `case_intelligence` utilisé pour le contexte/les
faits), tandis que la table `cases` référence clé sur un `uuid.UUID` —
le cast `uuid.UUID(case_id)` est fait une fois, explicitement, dans
`_resolve_owned_case_id` (`legal_drafting/api/routes.py`), avec un `404`
(jamais un `500`) si le format est invalide. Les autres routes
(`get_draft`, `.../versions`, `regenerate_*`, `restore_version`)
n'ont besoin d'aucune vérification d'appartenance dédiée : le store
scopé par `firm_id` garantit déjà qu'un `document_id` d'un autre cabinet
renvoie `None` (donc `404`, ou une liste de versions vide).

```mermaid
sequenceDiagram
    actor Avocat
    participant FE as Frontend (Next.js)
    participant Auth as /auth/login
    participant API as API REST
    participant CaseRepo as SqlAlchemyCaseRepository
    participant Store as SQLAlchemyDraftDocumentStore

    Avocat->>FE: email + mot de passe
    FE->>Auth: POST /auth/login
    Auth-->>FE: access_token (claims: sub, firm_id, role)
    FE->>FE: cookie httpOnly (jamais lu par le JS client)
    Avocat->>FE: créer un dossier
    FE->>API: POST /cases (Authorization: Bearer)
    API->>API: firm_id = get_current_firm_id(token)
    API-->>FE: Case{id, firm_id}
    Avocat->>FE: générer un brouillon pour ce dossier
    FE->>API: POST /legal-drafting/drafts {case_id}
    API->>CaseRepo: get_by_id(case_id, firm_id)
    CaseRepo-->>API: Case ou None (404 si None/autre cabinet)
    API->>Store: SQLAlchemyDraftDocumentStore(session, firm_id)
    API-->>FE: Document (scopé firm_id)
```

Frontend (`frontend/src/`) : `lib/session.ts` porte le cookie httpOnly
(jamais `localStorage`, jamais lu côté client — voir points de
vigilance), `lib/api.ts` l'injecte en `Authorization: Bearer` sur
chaque appel serveur (Server Components/Actions uniquement, aucun
fetch depuis le navigateur). `/login`, `/cases`, `/drafting`,
`/drafting/[id]` parlent à la vraie API ; c'est le chemin nominal
uniquement (pas de régénération de section, pas d'export, pas de
validation depuis l'UI ce sprint).

## Export

Trois formats, chacun préservant la structure et les citations — voir
docs/32-guide-exports.md : DOCX (`python-docx`), HTML (auto-suffisant),
et PDF (un writer minimal fait main, `export/pdf_writer.py`, faute de
bibliothèque d'écriture PDF dans les dépendances existantes — validé
par relecture via `pypdf`, déjà une dépendance du projet depuis le
Sprint 3).

## Observabilité

Chaque génération produit un `DraftMetrics` (durée, composants
utilisés, nombre de paragraphes, nombre de références, coût estimé via
`tmis.ai.evaluation.metrics.estimate_cost`, version de modèle utilisée)
— collecté par `DraftEvaluator`, même patron que
`tmis.legal_reasoning.evaluation.ReasoningEvaluator` (Sprint 6).

## API REST

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/api/v1/legal-drafting/drafts` | Crée un brouillon |
| `GET` | `/api/v1/legal-drafting/drafts/{id}` | Récupère un brouillon |
| `POST` | `.../sections/{key}/regenerate` | Régénère une section |
| `POST` | `.../sections/{key}/paragraphs/{id}/regenerate` | Régénère un paragraphe |
| `GET` | `.../versions` | Liste les versions |
| `GET` | `.../versions/compare?version_a=&version_b=` | Compare deux versions |
| `POST` | `.../versions/{n}/restore` | Restaure une version |
| `POST` | `.../validate` | Enregistre une décision humaine |
| `GET` | `.../review` | Constats de relecture |
| `GET` | `.../history` | Historique complet |
| `GET` | `.../export?format=docx\|pdf\|html` | Exporte le brouillon |

Documenté automatiquement via OpenAPI (`/openapi.json`, `/docs`).

## Portée du Sprint 7

- Chaque section produit aujourd'hui un seul paragraphe généré par le
  Kernel (sauf en-tête/signature, déterministes) — l'architecture
  (`Section.paragraphs: list[Paragraph]`) supporte déjà plusieurs
  paragraphes par section pour un futur sprint.
- Stockage en mémoire (`InMemoryDocumentStore`, historique,
  versioning), comme les moteurs précédents ; **mis à jour par la
  tranche `cases -> drafting`** — voir "Persistance & isolation
  multi-tenant" ci-dessus : `documents`/`versioning` sont désormais
  persistants et scopés par cabinet, `history`/`validation` restent en
  mémoire (dette documentée).
- Le Review Engine reste heuristique ; un moteur plus sophistiqué peut
  le remplacer derrière `ReviewEnginePort` sans toucher
  `DocumentOrchestrator`.
