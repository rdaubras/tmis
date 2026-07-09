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

## Méthode

Le projet est développé par sprints (voir
[`docs/09-roadmap-30-sprints.md`](./docs/09-roadmap-30-sprints.md)).
Chaque sprint livre du code fonctionnel et testé, met à jour la
documentation, et attend une validation avant de passer au suivant.
