# TMIS Frontend

Next.js (App Router) + TypeScript + Tailwind CSS + Shadcn UI. See `/docs`
at the repository root for the product vision and architecture.

## Development

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Structure

- `src/app/(app)/` — authenticated app shell and module routes (dossiers,
  documents, recherche, contrats, rédaction, chat, facturation,
  administration). Modules not yet implemented render a placeholder
  pointing to the sprint that delivers them (`docs/09-roadmap-30-sprints.md`).
- `src/components/ui/` — Shadcn UI primitives.
- `src/components/layout/` — sidebar/topbar app shell.
- `src/lib/nav-config.ts` — single source of truth for the module
  navigation.

## Tests

```bash
npm run lint
npm run build
```
