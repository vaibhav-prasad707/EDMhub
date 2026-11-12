# EDM Hub

EDM Hub is a fluorescent crate-digger for discovering electronic artists, guessing tracks, and tracking listening-game progress.

## Run & Operate

- `cd artifacts/api-server-python && python -m app.main` — run the API server (port from `PORT`, default 8080)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks from the OpenAPI spec
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- Frontend: pnpm workspaces, Node.js 24, TypeScript 5.9
- API: FastAPI (Python)
- DB: PostgreSQL + SQLModel
- API codegen: Orval (client hooks from OpenAPI spec)

## Where things live

- `artifacts/edm-hub/src/App.tsx` — routed web app and product interactions.
- `artifacts/edm-hub/src/index.css` — fluorescent zine theme, typography, motion, and responsive rules.
- `lib/api-spec/openapi.yaml` — source of truth for the artist, game, dashboard, and leaderboard API.
- `artifacts/api-server-python/app/api/edm.py` — EDM API handlers.
- `artifacts/api-server-python/app/lib/scoring.py` — game scoring.
- `artifacts/api-server-python/app/lib/edm_data.py` — seeded artist, track, genre, and question catalog.
- `artifacts/api-server-python/app/db/models.py` — PostgreSQL persistence for catalog, favorites, games, and rounds.

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
- The FastAPI routes and response shapes must match `openapi.yaml` by hand; there is no server-side codegen.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
