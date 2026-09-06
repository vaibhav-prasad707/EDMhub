# EDM Hub

EDM Hub is a fluorescent crate-digger for discovering electronic artists, guessing tracks, and tracking listening-game progress.

The project is a full-stack TypeScript application with a React/Vite frontend, an Express API, PostgreSQL persistence, and generated OpenAPI client types.

<img width="1526" height="787" alt="Screenshot 2026-09-06 at 16 05 23" src="https://github.com/user-attachments/assets/dee8d8ff-da24-4b6a-9b6e-f712100da3c7" />


## Features

- Artist discovery with search, genre filters, recommendations, and artist details
- Favorite artists and a personal library
- Song-guessing game with difficulty levels, hints, streaks, time bonuses, and scoring
- Dashboard with listening-game stats, genre breakdowns, achievements, and recent activity
- Profile and all-time leaderboard views
- Persistent favorites, game sessions, and game rounds
- Fluorescent editorial/zine-inspired visual system
- Same-origin local API proxy for normal desktop development

## Current data source

The initial catalog is seeded locally in:

```text
artifacts/api-server/src/lib/edm-data.ts
```

The API inserts this catalog into PostgreSQL on first use. Artist and track discovery currently reads from the seeded TypeScript catalog, while favorites and game activity are persisted in PostgreSQL.

Spotify import/synchronization is not currently enabled. Do not put Spotify credentials in frontend code or commit them to this repository. A future server-side importer should use the Spotify Client Credentials flow and upsert Spotify artist and track IDs into the database.

## Tech stack

- Node.js 24
- pnpm 10
- React 19
- Vite 7
- Express 5
- PostgreSQL
- Drizzle ORM
- Zod 4
- OpenAPI and generated React Query hooks
- Tailwind CSS 4
- Framer Motion

## Repository layout

```text
artifacts/
  api-server/       Express API server
  edm-hub/          React/Vite web application
  mockup-sandbox/   Component preview server

lib/
  api-client-react/ Generated React Query API client
  api-spec/         OpenAPI source specification and code generation
  api-zod/          Generated server validation schemas
  db/               Drizzle schema and database client

attached_assets/    Supplied design references and project assets
```

## Requirements

Install the following before starting:

- Node.js 24.x
- pnpm 10.x
- PostgreSQL 14 or newer

Check your versions:

```bash
node --version
pnpm --version
```

## Local setup

### 1. Install dependencies

From the repository root:

```bash
corepack enable
corepack prepare pnpm@10.26.1 --activate
pnpm install
```

### 2. Create a PostgreSQL database

Create a database named `edm_hub`:

```bash
createdb edm_hub
```

If the `createdb` command is unavailable, create the database through `psql` or pgAdmin:

```bash
psql -U postgres -c "CREATE DATABASE edm_hub;"
```

Set the connection string in the terminal where the API will run:

```bash
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/edm_hub"
```

If your local PostgreSQL server does not require a password, use:

```bash
export DATABASE_URL="postgresql://postgres@localhost:5432/edm_hub"
```

### 3. Create or update the database tables

```bash
pnpm --filter @workspace/db run push
```

This creates the EDM Hub tables:

- `edm_artists`
- `edm_tracks`
- `edm_favorites`
- `edm_game_sessions`
- `edm_game_rounds`

### 4. Start the API server

Open one terminal and run:

```bash
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/edm_hub"
export PORT=8080

pnpm --filter @workspace/api-server run dev
```

Keep this terminal open.

Verify the API is running:

```bash
curl http://localhost:8080/api/healthz
```

### 5. Start the frontend

Open a second terminal in the repository root:

```bash
export PORT=18796
export BASE_PATH=/

pnpm --filter @workspace/edm-hub run dev
```

Open the application at:

```text
http://localhost:18796/
```

The Vite development server forwards `/api` requests to the API at `http://localhost:8080`, so both terminals must remain running.

## Windows PowerShell setup

Use these equivalents instead of `export`:

```powershell
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/edm_hub"
$env:PORT="8080"
pnpm --filter @workspace/api-server run dev
```

In a second PowerShell window:

```powershell
$env:PORT="18796"
$env:BASE_PATH="/"
pnpm --filter @workspace/edm-hub run dev
```

## Useful commands

Run the full workspace typecheck:

```bash
pnpm run typecheck
```

Build all packages:

```bash
pnpm run build
```

Build the frontend:

```bash
PORT=18796 BASE_PATH=/ pnpm --filter @workspace/edm-hub run build
```

Build the API:

```bash
pnpm --filter @workspace/api-server run build
```

Regenerate typed API clients after changing the OpenAPI specification:

```bash
pnpm --filter @workspace/api-spec run codegen
```

Update the development database after changing the Drizzle schema:

```bash
pnpm --filter @workspace/db run push
```

## Environment variables

| Variable | Required by | Description |
| --- | --- | --- |
| `DATABASE_URL` | API and database tooling | PostgreSQL connection string |
| `PORT` | API or frontend | Port for the process being started |
| `BASE_PATH` | Frontend | Vite base path; use `/` for a normal local install |
| `NODE_ENV` | API | Set automatically by the API `dev` script |

Never commit database credentials, API keys, or client secrets. Use your local shell environment, an ignored `.env` file loaded by your own tooling, or your deployment provider’s secret manager.

## Troubleshooting

### Missing `lightningcss.darwin-arm64.node`

This usually means dependencies were installed before the project included macOS ARM optional binaries. From the repository root:

```bash
rm -rf node_modules
pnpm install
```

Then restart the frontend.

### `PORT environment variable is required`

The Vite and API configurations intentionally require an explicit port:

```bash
# API
PORT=8080

# Frontend
PORT=18796
BASE_PATH=/
```

### `DATABASE_URL must be set`

Set `DATABASE_URL` in the same terminal that starts the API server. Environment variables set in one terminal are not automatically available in another terminal.

### `createdb: command not found`

Install PostgreSQL command-line tools or create the database using pgAdmin. The application only needs a valid PostgreSQL connection string.

### The API starts but the frontend shows request errors

Confirm that:

1. The API is running on port `8080`.
2. The frontend is running on port `18796`.
3. The frontend was started with `BASE_PATH=/`.
4. PostgreSQL is running and `DATABASE_URL` points to the correct database.

## Architecture notes

- `lib/api-spec/openapi.yaml` is the source of truth for API contracts.
- Generated API hooks and validation schemas should be regenerated after OpenAPI changes.
- The API currently uses a demo user ID (`demo-dj`) because authentication has not yet been added.
- The current product catalog is seeded data; PostgreSQL persists user-facing game and favorite state.
- Spotify credentials, when eventually used, must stay in the API process and must never be exposed to the React application.

## License

The project is marked as MIT in the root package metadata.
