# TMIS — Themis Intelligence System

TMIS est un **AI Legal Operating System** : une plateforme SaaS qui
accompagne l'avocat sur l'intégralité du cycle de vie d'un dossier,
sans jamais décider à sa place.

## Documentation

La documentation complète (vision, architecture fonctionnelle et
technique, DDD, stratégies multi-agents/RAG/sécurité, plan de tests,
roadmap des 30 sprints) se trouve dans [`docs/`](./docs/README.md).

## Structure du dépôt

```
tmis/
├── backend/    # API FastAPI (Clean Architecture / DDD, agents LangGraph)
├── frontend/   # Next.js (App Router) + TypeScript + Tailwind + Shadcn UI
├── docs/       # Vision, architecture, stratégies, roadmap
└── docker-compose.yml
```

## Démarrage rapide (développement)

```bash
docker compose up --build
```

- Backend : http://localhost:8000 (docs OpenAPI sur `/docs`)
- Frontend : http://localhost:3000

Voir `backend/README.md` et `frontend/README.md` pour un développement
sans Docker.

### Variables d'environnement

- **Frontend** (côté serveur uniquement — jamais exposée au navigateur) :
  `TMIS_API_BASE_URL`, l'URL du backend vue par le serveur Next.js
  (`http://backend:8000` sous Docker Compose, voir
  `frontend/.env.example`). `NEXT_PUBLIC_API_URL` n'existe pas dans ce
  projet : le frontend n'appelle jamais l'API directement depuis le
  navigateur (voir `frontend/src/lib/api.ts`, `frontend/src/lib/auth.ts`).
- **Backend** (voir `backend/.env.example`) : `TMIS_DATABASE_URL`,
  `TMIS_REDIS_URL`, `TMIS_JWT_SECRET_KEY` (≥ 32 caractères aléatoires
  hors `TMIS_DEBUG=true`), `TMIS_LICENSE_SIGNING_KEY` et
  `TMIS_PLUGIN_SIGNING_KEY` (doivent être remplacées, hors mode debug —
  le démarrage refuse la valeur par défaut, voir
  `tmis.core.config.Settings`).

## Méthode

Le projet est développé par sprints (voir
[`docs/09-roadmap-30-sprints.md`](./docs/09-roadmap-30-sprints.md)).
Chaque sprint livre du code fonctionnel et testé, met à jour la
documentation, et attend une validation avant de passer au suivant.
