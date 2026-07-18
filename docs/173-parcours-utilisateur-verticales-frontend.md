# 173 — Parcours utilisateur : surfacer les verticales (frontend)

> Sprint "Surfacer les verticales" (points 1 à 5 de l'audit produit) : cinq
> écrans passent de coquille (`ModulePlaceholder`) à outil consommant l'API
> existante. Zéro nouveau backend — voir les contrats détaillés dans les
> docs de chaque slice (21, 19, 28, 14).

## Socle (T0)

- `frontend/src/lib/api.ts` — un seul point d'accès API server-only
  (`apiFetch`), plus deux variantes (ADR-FE-02) : `apiFetchMultipart`
  (upload) et `apiFetchBinary` (export). Toute page qui a besoin de
  données backend importe un helper typé de ce fichier, jamais un
  `fetch()` brut.
- `frontend/src/lib/document-status.ts` — le seul endroit qui connaît les
  statuts terminaux de traitement documentaire (`processed`/`failed`) ;
  séparé de `lib/api.ts` car ce dernier est `server-only` et ne peut pas
  être importé par un composant client.
- Composants réutilisés sur les 5 pages : `EmptyState`, `RouteError`
  (derrière chaque `error.tsx`), `Skeleton` (derrière chaque
  `loading.tsx`), `ScoreBadge` (score/confiance 0..1 → %), `StatusBadge`
  (statut générique par domaine), `CitationCard` (source vérifiable).

## Écrans

| Écran | Route | API consommée |
| --- | --- | --- |
| Recherche documentaire | `/research` | `POST /legal-research/search`, `GET /legal-research/history` |
| Dossiers | `/cases` | `GET /cases`, `POST /cases` |
| Dossier 360 | `/cases/[id]` | `GET /cases/{id}`, `GET/POST /cases/{id}/profile`, `GET /cases/{id}/timeline`, `GET /cases/{id}/analysis` (à la demande) |
| Rédaction — création | `/drafting` | `GET /cases`, `POST /legal-drafting/drafts` |
| Rédaction — éditeur | `/drafting/[id]` | `GET /legal-drafting/drafts/{id}`, `GET .../versions`, `GET .../versions/compare`, `POST .../validate`, `GET .../export` |
| Documents — dépôt | `/documents` | `GET /cases`, `GET /cases/{id}/profile` (liste), `POST /documents/upload` |
| Documents — détail | `/documents/[id]` | `GET /documents/{id}`, `GET .../versions`, `GET .../analysis` (à la demande) |
| Tableau de bord | `/dashboard` | `GET /cases`, `GET /legal-research/history` |

## Points d'attention repris de la spec

- **Upload asynchrone** (`/documents/[id]`) : le statut renvoyé par
  `POST /documents/upload` est `received`, jamais un état final. Le
  composant client `status-poller.tsx` réappelle `router.refresh()`
  toutes les 3 s tant que `documentIsReady(status)` est faux — la page ne
  fige jamais sur un statut "terminé" fictif.
- **Export binaire** (`/drafting/[id]`) : `exportDraftAction` (Server
  Action) lit les octets côté serveur (cookie httpOnly oblige) et les
  renvoie encodés en base64 ; `export-buttons.tsx` (Client Component) les
  décode en `Blob` et déclenche le téléchargement — jamais de `.json()`
  sur cette réponse.
- **Incohérences de chronologie** : `TimelineInconsistency` n'est exposé
  par aucun endpoint dédié — uniquement dans `result.inconsistencies` de
  `GET /cases/{id}/analysis`, un calcul multi-agents coûteux. L'onglet
  Chronologie ne le déclenche donc que sur action explicite ("Détecter
  les incohérences"), jamais automatiquement.
- **401** : toujours géré par `apiFetch` (redirection `/login`) ; aucune
  des pages ci-dessus ne fait son propre `fetch`.

## Limite backend connue (documentée, non contournée)

Il n'existe pas d'endpoint de listing des brouillons (`GET
/legal-drafting/drafts`). Le tableau de bord ne peut donc pas afficher de
"brouillons en cours" réel sans inventer un nouvel endpoint — hors
périmètre de ce sprint (voir § 3 "Out"). Le tableau de bord affiche à la
place les dossiers et recherches récents (données réellement
disponibles) plus un accès rapide vers la rédaction.
