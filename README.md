# EDM Hub

**A neon-brutalist discovery playground for electronic dance music fans. Dig through artists, play a song-guessing game, build playlists, and track your stats.**

React + Vite frontend, FastAPI backend, PostgreSQL, and a generated OpenAPI client.

<img width="1526" height="787" alt="Screenshot 2026-09-06 at 16 05 23" src="https://github.com/user-attachments/assets/dee8d8ff-da24-4b6a-9b6e-f712100da3c7" />

## Features

- **Discover:** search artists, filter by genre, get recommendations, favorite artists.
- **Guess the Track:** 5, 10 or 20 rounds of 12-second clips with four choices. Filter by genre, era or a single artist. Hints, streaks, speed bonuses, and a scorecard at the end. Answers stay on the server.
- **My Library:** create playlists, search any artist or song from a dropdown, add songs, and play them as a queue.
- **Accounts:** sign up with a username, email and password, then sign in with your username and password.
- **Dashboard, profile and leaderboard.**

## Quick start

You need Node 24, pnpm 10, Python 3.12+ and PostgreSQL 14+.

```bash
# 1. Install
pnpm install
python3 -m venv artifacts/api-server-python/.venv
artifacts/api-server-python/.venv/bin/pip install -r artifacts/api-server-python/requirements.txt

# 2. Database
createdb edm_hub

# 3. Configure the API
cp artifacts/api-server-python/.env.example artifacts/api-server-python/.env
# Edit .env: set DATABASE_URL and JWT_SECRET (32+ characters)

# 4. Run the API (terminal 1)
cd artifacts/api-server-python
PORT=8080 .venv/bin/python -m app.main

# 5. Run the frontend (terminal 2, from the repo root)
PORT=18796 BASE_PATH=/ pnpm --filter @workspace/edm-hub run dev
```

Open **http://127.0.0.1:18796**. The dev server proxies `/api` to the API on port 8080. Tables are created automatically on startup.

On Windows PowerShell, set variables with `$env:PORT="8080"` instead of `PORT=8080`.

## Getting songs

A small built-in seed lets the app run on first start. The real catalog comes from Spotify:

```bash
cd artifacts/api-server-python
.venv/bin/python -m app.scripts.sync_spotify                  # import every curated artist (slow the first time)
.venv/bin/python -m app.scripts.sync_spotify --genre Techno   # one genre
.venv/bin/python -m app.scripts.sync_spotify --refresh        # re-fetch artists already imported
```

- To add an artist, put their exact Spotify name in `app/lib/curated_artists.py` and re-run the sync. It only downloads new artists and is safe to re-run.
- Spotify no longer provides previews to new apps, so 30-second clips come from the iTunes Search API. Songs with no match stay in the catalog but are left out of the game.
- Add your Spotify credentials (`SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`) to `.env`. They never reach the browser.

## Playback

- Everyone hears the 30-second previews. The game always uses these.
- To stream full tracks, click **Connect** in the sidebar to link Spotify. This needs **Spotify Premium**, and while your Spotify app is in Development Mode the account must be added under *User Management* in the Spotify dashboard.
- In the Spotify dashboard, add the redirect URI `http://127.0.0.1:18796/api/spotify/callback`. Spotify does not allow `localhost`, so open the app at `127.0.0.1`.

## Environment variables

Set these in `artifacts/api-server-python/.env`.

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://postgres:pw@localhost:5432/edm_hub` |
| `JWT_SECRET` | Signs session cookies. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `COOKIE_SECURE` | `true` when served over HTTPS (default `false`) |
| `SPOTIPY_CLIENT_ID` / `SPOTIPY_CLIENT_SECRET` | Spotify app credentials (keep secret) |
| `SPOTIFY_REDIRECT_URI` | Defaults to `http://127.0.0.1:18796/api/spotify/callback` |

## Repository layout

```text
artifacts/
  api-server-python/   FastAPI backend (app/api = routes, app/lib = game and catalog logic)
  edm-hub/             React/Vite frontend
lib/
  api-spec/            openapi.yaml (source of truth for the API) and codegen
  api-client-react/    Generated React Query client
```

## Useful commands

```bash
pnpm run typecheck                                  # typecheck the workspace
pnpm --filter @workspace/api-spec run codegen       # regenerate the API client after editing openapi.yaml
PORT=18796 BASE_PATH=/ pnpm --filter @workspace/edm-hub run build
```

When you add or change an API route in `app/api/`, update `lib/api-spec/openapi.yaml` by hand and re-run codegen.

## Troubleshooting

- **`PORT environment variable is required`:** start the frontend with `PORT=18796 BASE_PATH=/`.
- **`DATABASE_URL` or `JWT_SECRET` errors:** set both in `artifacts/api-server-python/.env`.
- **Frontend shows request errors:** check the API is running on 8080, the frontend on 18796, and PostgreSQL is up.
- **`redirect_uri: Not matching configuration` from Spotify:** the URI in the Spotify dashboard must match `SPOTIFY_REDIRECT_URI` exactly.
- **`lightningcss.darwin-arm64.node` missing:** run `rm -rf node_modules && pnpm install`.
- **The API doesn't pick up code changes:** it has no auto-reload, so restart it.

## Deploying

Use a managed Postgres (Neon or Supabase) and set its URL as `DATABASE_URL`. Host the API on Render or Railway with root directory `artifacts/api-server-python`, build command `pip install -r requirements.txt`, and start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Host the frontend on Vercel with root `artifacts/edm-hub`, and add a `vercel.json` rewrite that sends `/api/(.*)` to your API URL. Set `COOKIE_SECURE=true` and register your production Spotify redirect URI.

## License

MIT
