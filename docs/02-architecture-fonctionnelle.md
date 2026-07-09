# Architecture fonctionnelle

## Vue d'ensemble des modules (V1)

```mermaid
flowchart TB
    subgraph Core["Socle Cabinet"]
        M1[Gestion des cabinets]
        M2[Gestion des utilisateurs]
        M3[Administration]
        M4[Facturation]
    end

    subgraph CaseMgmt["Gestion de dossiers"]
        M5[Gestion des dossiers]
        M6[Documents]
        M7[OCR]
        M8[Chronologie]
    end

    subgraph Intelligence["Intelligence juridique"]
        M9[Chat IA]
        M10[Recherche documentaire]
        M11[Analyse IA]
        M12[Contrats]
        M13[Rédaction]
    end

    subgraph Pilotage["Pilotage"]
        M14[Tableau de bord]
    end

    Core --> CaseMgmt
    CaseMgmt --> Intelligence
    Intelligence --> Pilotage
```

## Modules et responsabilités

| Module | Responsabilité | Bounded context DDD |
|---|---|---|
| Gestion des cabinets | Création/paramétrage d'un tenant cabinet, marque blanche, offres | `firm` |
| Gestion des utilisateurs | Comptes, rôles, permissions, MFA, invitations | `identity` |
| Gestion des dossiers | Cycle de vie d'un dossier, parties, phases, statuts | `case` |
| Documents | Stockage, versionning, classification des pièces | `document` |
| OCR | Extraction de texte depuis PDF/scans/images | `ocr` |
| Chat IA | Interface conversationnelle multi-agents sur un dossier | `assistant` |
| Recherche documentaire | Connecteurs vers sources juridiques configurables | `legal_research` |
| Analyse IA | Extraction d'entités, incohérences, chronologie automatique | `case_analysis` |
| Chronologie | Construction et édition de frises chronologiques | `timeline` |
| Contrats | Analyse, comparaison, détection de risques contractuels | `contract` |
| Rédaction | Génération de brouillons (consultations, conclusions...) | `drafting` |
| Tableau de bord | Vue synthétique cabinet / dossier / utilisateur | `dashboard` |
| Facturation | Abonnements, usage, Stripe, quotas | `billing` |
| Administration | Supervision, audit, configuration globale | `platform_admin` |

## Parcours utilisateur clé : analyse d'un nouveau dossier

```mermaid
sequenceDiagram
    actor Avocat
    participant UI as Frontend (Next.js)
    participant API as API Gateway (FastAPI)
    participant Orch as Chef d'Orchestre (LangGraph)
    participant OCR as Agent OCR/Ingestion
    participant Analyse as Agent Analyse
    participant Verif as Agent Vérificateur
    participant RAG as RAG (Qdrant)

    Avocat->>UI: Crée un dossier + dépose des pièces
    UI->>API: POST /cases/{id}/documents
    API->>OCR: Ingestion asynchrone (Celery)
    OCR->>RAG: Indexation (chunks + embeddings)
    Avocat->>UI: Demande "Analyser ce dossier"
    UI->>API: POST /cases/{id}/analysis
    API->>Orch: Découpe la tâche
    Orch->>Analyse: Extraire entités, faits, dates
    Analyse->>RAG: Recherche hybride (contexte dossier)
    Orch->>Verif: Vérifier cohérence & citations
    Verif-->>Orch: Rapport validé + limites signalées
    Orch-->>API: Synthèse + chronologie + sources
    API-->>UI: Résultat affiché avec citations cliquables
    UI-->>Avocat: Analyse consultable, à valider
```

## Cycle de vie d'un dossier

```mermaid
stateDiagram-v2
    [*] --> Ouvert
    Ouvert --> EnCoursAnalyse: Import de pièces
    EnCoursAnalyse --> EnCoursRedaction: Analyse validée
    EnCoursRedaction --> EnAttenteValidation: Brouillon généré
    EnAttenteValidation --> EnCoursRedaction: Modifications demandées
    EnAttenteValidation --> Clos: Validation avocat
    Clos --> Archive
    Archive --> [*]
```

## Extensibilité multi-métiers (post-V1)

L'architecture modulaire (voir `03-architecture-technique.md`) permet
d'ajouter de futurs modules métiers (notaires, experts-comptables,
directions juridiques) comme de **nouveaux bounded contexts** branchés sur
le même socle (identity, firm, billing, RAG, agents) sans modifier le
noyau existant. Ce point n'est pas développé en V1.
