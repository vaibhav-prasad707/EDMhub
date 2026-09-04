# EDM Hub

EDM Hub is a fluorescent crate-digger for discovering electronic artists, guessing tracks, and tracking listening-game progress.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `artifacts/edm-hub/src/App.tsx` — routed web app and product interactions.
- `artifacts/edm-hub/src/index.css` — fluorescent zine theme, typography, motion, and responsive rules.
- `lib/api-spec/openapi.yaml` — source of truth for the artist, game, dashboard, and leaderboard API.
- `artifacts/api-server/src/routes/edm.ts` — EDM API handlers and demo game scoring.
- `artifacts/api-server/src/lib/edm-data.ts` — seeded artist, track, genre, and question catalog.
- `lib/db/src/schema/edm.ts` — PostgreSQL persistence for catalog, favorites, games, and rounds.

## Architecture decisions

- The web app uses the shared API server and generated React Query hooks rather than a frontend-only mock.
- The first build uses a stable demo DJ profile while keeping favorites and game sessions persisted in PostgreSQL.
- The visual language follows the supplied fluorescent zine reference instead of copying Spotify's default dark UI.
- Catalog rows are seeded locally so the product is useful before a Spotify connector is available.

## Product

- Artist discovery with genre filters, search, recommendations, artist details, and favorites.
- A difficulty-based song guessing game with hints, streaks, time bonuses, and results.
- Dashboard, library, profile, achievements, recent activity, and all-time leaderboard views.

## User preferences

- Apply the supplied extreme fluorescent zine direction while building EDM Hub.

## Gotchas

- Regenerate the typed client and validation schemas after changing `lib/api-spec/openapi.yaml`.
- The generated Zod validation package requires Zod 4 because current Orval output uses `zod.int()`.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
