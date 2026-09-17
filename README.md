# EDM Hub

**EDM Hub is a neon-brutalist discovery playground for electronic music fans. Dig through emerging and iconic artists, test your track knowledge in fast-paced guessing games, save your favorites, and build a personal profile of the sounds that keep you moving.**

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


## To do

# EDM Hub: Deployment Guide & Development Roadmap

The UI layout of EDM Hub presents a phenomenal fluorescent editorial/zine aesthetic that is incredibly clean and stands out perfectly for an electronic music platform.

Given your current workspace setup (pnpm monorepo, React 19, Express 5, Drizzle ORM) and feature backlog, this guide provides the exact steps to deploy your partial build today and safely build the remaining features.

---

## Table of Contents

- [Part 1: Deploying the Partial Build Today](#part-1-deploying-the-partial-build-today)
  - [Database Setup](#database-setup)
  - [Backend API Deployment](#backend-api-deployment)
  - [Frontend Deployment](#frontend-deployment)
- [Part 2: Development Roadmap](#part-2-development-roadmap)
  - [Phase 1: Player Verification](#phase-1-check-if-the-player-works)
  - [Phase 2: User Login & Authentication](#phase-2-add-user-login--auth)
  - [Phase 3: Song Guessing Game](#phase-3-build-the-song-guessing-game)
  - [Phase 4: Spotify Integration](#phase-4-connect-a-real-time-music-api-spotify)

---

## Part 1: Deploying the Partial Build Today

Since your project uses a monorepo layout with pnpm workspaces, avoid hosting on a single rigid server. Instead, split deployment across free-tier services and scale efficiently.

### Database Setup

**Platform:** Supabase or Neon

Since you are using PostgreSQL and Drizzle, do not host your own database. Both Supabase and Neon offer free managed Postgres instances.

**Steps:**

1. Sign up for **Supabase** or **Neon**
2. Copy your production connection string
3. Add it to your environment variables as `DATABASE_URL`
4. Run your schema migration from your local machine to production:

```bash
DATABASE_URL="your-production-string" pnpm --filter @workspace/db run push
```

**Key Point:** Use managed database services to eliminate operational overhead and ensure reliability.

---

### Backend API Deployment

**Platform:** Render or Railway

Your backend is an Express 5 app. Both Render and Railway handle Node.js/pnpm monorepos natively.

**Steps:**

1. Create a web service on Render or Railway
2. Link your GitHub repository
3. Configure the build and start commands:

**Build Command:**

```bash
pnpm run build
```

Or to build only the API service:

```bash
pnpm --filter @workspace/api-server run build
```

**Start Command:**

```bash
pnpm --filter @workspace/api-server start
```

Adjust the filter to match your actual workspace name.

4. Set environment variables in the platform dashboard:
   - `PORT=8080`
   - `DATABASE_URL` (your production connection string)
   - Any other required API environment variables

**Key Point:** The monorepo structure is fully supported; just ensure your workspace filter references are correct.

---

### Frontend Deployment

**Platform:** Vercel

Vercel is the easiest place to host your React/Vite frontend.

**Steps:**

1. Import your repository into Vercel
2. Set the **Root Directory** to: `artifacts/edm-hub`
3. Vercel will automatically detect Vite and configure the build
4. Set environment variables in the Vercel dashboard:
   - `PORT=18796`
   - `BASE_PATH=/`
5. Configure API proxy to your live backend:

**vercel.json** (in `artifacts/edm-hub/` root):

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-render-or-railway-url.com/api/$1"
    }
  ]
}
```

Replace `https://your-render-or-railway-url.com` with your actual backend URL.

**Key Point:** This proxy configuration keeps your frontend architecture clean and maintains same-origin requests, simplifying CORS configuration.

---

## Part 2: Development Roadmap

Do not try to build all remaining features at once. Follow this sequential order to prevent breaking your architectural layout and ensure a stable release cycle.

---

## Phase 1: Check if the Player Works

**Objective:** Verify that your local frontend audio player functions correctly with real audio sources.

**Why:** Before integrating Spotify or other complex APIs, ensure the core player functionality works end-to-end.

### Implementation Steps

1. **Locate your seeding data file:**

```
artifacts/api-server/src/lib/edm-data.ts
```

2. **Replace audio sources with open-source URLs:**

Find the track entries and update their `audio_source` field with royalty-free MP3 URLs from sources like:
   - Pixabay Music
   - Free Music Archive
   - Other open-source music repositories

Example update:

```typescript
{
  id: 1,
  title: "Track Name",
  artist: "Artist Name",
  audio_source: "https://pixabay.com/music/tracks/example-track.mp3",
  // ... other fields
}
```

3. **Test locally:**

- Start your frontend development server
- Navigate to the dashboard
- Click "Play" on any track
- Verify the global player state updates (Night Shift Radio stream component)
- Confirm audio plays through your speakers

### Success Criteria

- Player UI reflects the currently playing track
- Audio streams without errors
- Player controls (play, pause, volume) function correctly
- State persists across navigation

---

## Phase 2: Add User Login & Auth

**Objective:** Replace hardcoded demo user ID with a real database-backed authentication system.

**Why:** Your project currently hardcodes a demo user ID (`demo-dj`). Real user data (favorites, game sessions, etc.) requires proper authentication.

### Implementation Approach

**Do not build crypto password-hashing from scratch.** Use one of these options:

- **Lucia Auth** (lightweight, pairs perfectly with Drizzle ORM)
- **Clerk** (managed, modern UX, zero backend work)
- **Auth0** (enterprise-ready, battle-tested)

### Database Schema Updates

**Update Drizzle schema** (`lib/db`) to add a `users` table:

```typescript
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  username: varchar('username', { length: 255 }).notNull().unique(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  password_hash: varchar('password_hash', { length: 255 }), // if using Lucia
  created_at: timestamp('created_at').defaultNow(),
  updated_at: timestamp('updated_at').defaultNow(),
});

// Update existing tables to reference real user_id
export const edm_favorites = pgTable('edm_favorites', {
  id: serial('id').primaryKey(),
  user_id: integer('user_id').references(() => users.id).notNull(),
  track_id: integer('track_id').references(() => edm_tracks.id).notNull(),
  created_at: timestamp('created_at').defaultNow(),
});

export const edm_game_sessions = pgTable('edm_game_sessions', {
  id: serial('id').primaryKey(),
  user_id: integer('user_id').references(() => users.id).notNull(),
  accuracy: decimal('accuracy'),
  games_played: integer('games_played').default(0),
  created_at: timestamp('created_at').defaultNow(),
});
```

### API Changes

- Add login/signup endpoints to your Express API
- Extract `user_id` from the authenticated session
- Replace hardcoded `demo-dj` references with real user IDs
- Protect endpoints that modify user data with authentication middleware

### Success Criteria

- Users can create accounts and log in
- User data (favorites, game sessions) is isolated per user
- Authentication state persists across sessions
- Favorites/game data updates correctly for the logged-in user

---

## Phase 3: Build the Song Guessing Game

**Objective:** Make the guessing game route fully functional and integrated with your database.

**Why:** Your dashboard already displays stats for "Games Played" and "Accuracy" (showing 86%). Now you need to make these stats meaningful and tied to real gameplay.

### Game Flow

1. Fetch a random track from your Drizzle `edm_tracks` table
2. Stream a short 10-second snippet through your working player
3. Present multiple choice options (4 options) or text input powered by existing backend search
4. Validate the user's answer
5. Save round results to `edm_game_rounds` table

### Implementation Steps

**1. Create a dedicated route/page:**

```
artifacts/edm-hub/src/pages/Guess.tsx
or
artifacts/edm-hub/src/routes/guess
```

**2. Backend endpoint for fetching a random track:**

```typescript
// Express API
app.get('/api/game/random-track', async (req, res) => {
  const randomTrack = await db
    .select()
    .from(edm_tracks)
    .orderBy(sql`RANDOM()`)
    .limit(1);
  
  res.json(randomTrack[0]);
});
```

**3. Frontend game logic:**

```typescript
// Fetch random track
const track = await fetch('/api/game/random-track').then(r => r.json());

// Play 10-second snippet
player.play(track.audio_source, { duration: 10000 });

// Show 4 multiple-choice options or text input
// User selects/submits answer

// Validate answer
const isCorrect = answer === track.title || answer === track.id;

// Save game round
await fetch('/api/game/rounds', {
  method: 'POST',
  body: JSON.stringify({
    user_id: currentUser.id,
    track_id: track.id,
    guess: answer,
    correct: isCorrect,
  }),
});

// Update game stats
updateGameStats();
```

**4. Database table for game rounds:**

```typescript
export const edm_game_rounds = pgTable('edm_game_rounds', {
  id: serial('id').primaryKey(),
  user_id: integer('user_id').references(() => users.id).notNull(),
  track_id: integer('track_id').references(() => edm_tracks.id).notNull(),
  guess: varchar('guess', { length: 255 }).notNull(),
  correct: boolean('correct').notNull(),
  created_at: timestamp('created_at').defaultNow(),
});
```

### Success Criteria

- User can start a game round
- 10-second audio snippet plays correctly
- Multiple-choice options or search input displays
- User answer is validated
- Game stats (Games Played, Accuracy) update in real time
- Round history is saved to database

---

## Phase 4: Connect a Real-Time Music API (Spotify)

**Objective:** Integrate Spotify API to populate your track database with high-quality EDM content.

**Why:** Your current data is seeded locally. Spotify provides a massive, up-to-date catalog of electronic music with rich metadata.

### Critical Security Rule

**Never put Spotify credentials in your frontend code.**

All Spotify integration logic must be completely isolated in your Express API server (`artifacts/api-server/`).

### Implementation Architecture

**1. Register application on Spotify Developer Dashboard:**

- Go to https://developer.spotify.com/dashboard
- Create a new application
- Obtain your `Client ID` and `Client Secret`
- Add these to your backend `.env` file (never in frontend)

**2. Implement Spotify Client Credentials Flow in Express:**

```typescript
// artifacts/api-server/src/spotify.ts
import axios from 'axios';

const SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/api/token';
const SPOTIFY_API_URL = 'https://api.spotify.com/v1';

let cachedAccessToken: string | null = null;
let tokenExpiry: number = 0;

async function getSpotifyAccessToken(): Promise<string> {
  const now = Date.now();
  
  // Return cached token if still valid
  if (cachedAccessToken && now < tokenExpiry) {
    return cachedAccessToken;
  }

  const response = await axios.post(SPOTIFY_AUTH_URL, null, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    auth: {
      username: process.env.SPOTIFY_CLIENT_ID!,
      password: process.env.SPOTIFY_CLIENT_SECRET!,
    },
    data: 'grant_type=client_credentials',
  });

  cachedAccessToken = response.data.access_token;
  tokenExpiry = now + response.data.expires_in * 1000;

  return cachedAccessToken;
}

export async function fetchSpotifyTracks(query: string, limit = 20) {
  const token = await getSpotifyAccessToken();

  const response = await axios.get(
    `${SPOTIFY_API_URL}/search`,
    {
      params: {
        q: query,
        type: 'track',
        limit,
      },
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data.tracks.items;
}
```

**3. Create an admin endpoint to sync tracks:**

```typescript
// artifacts/api-server/src/routes/admin.ts
app.post('/api/admin/sync-spotify', async (req, res) => {
  try {
    // Fetch curated EDM playlists or search results from Spotify
    const tracks = await fetchSpotifyTracks('electronic music', 100);

    // Transform Spotify metadata to match your Drizzle schema
    const formatted = tracks.map((track: any) => ({
      title: track.name,
      artist: track.artists[0].name,
      album: track.album.name,
      duration_ms: track.duration_ms,
      spotify_id: track.id,
      audio_preview_url: track.preview_url,
      cover_art_url: track.album.images[0]?.url,
      // ... map other fields as needed
    }));

    // Insert/update tracks in your Postgres database
    for (const track of formatted) {
      await db
        .insert(edm_tracks)
        .values(track)
        .onConflictDoUpdate({
          target: edm_tracks.spotify_id,
          set: track,
        });
    }

    res.json({ synced: formatted.length });
  } catch (error) {
    console.error('Spotify sync failed:', error);
    res.status(500).json({ error: 'Sync failed' });
  }
});
```

**4. Frontend continues reading from your API:**

Your frontend does NOT need to know about Spotify. It simply reads from your own API:

```typescript
// Frontend code
const tracks = await fetch('/api/tracks').then(r => r.json());
// Play from your own database
player.play(tracks[0].audio_preview_url);
```

### Security Best Practices

- Store `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` only in backend `.env`
- Never expose these credentials in API responses or frontend code
- Use environment variable validation to catch missing credentials at startup
- Implement rate limiting on the `/api/admin/sync-spotify` endpoint
- Only allow authenticated admin users to trigger syncs

### Success Criteria

- Spotify tracks are successfully fetched and stored in your database
- Track metadata (artist, album, duration, etc.) is accurately imported
- Audio preview URLs are preserved and playable
- The sync process can be run repeatedly without duplicating tracks
- Frontend continues to work seamlessly with the new Spotify-sourced data

---

## Deployment Checklist

Before deploying each phase, verify:

- [ ] All environment variables are set correctly in the deployment platform
- [ ] Database migrations have been applied to production
- [ ] API endpoints are accessible and responding correctly
- [ ] Frontend can communicate with the backend API
- [ ] Error handling and logging are in place
- [ ] Security best practices are followed (especially for Phase 4)
- [ ] User-facing features have been tested in a staging environment

---

## Deployment Sequence Recommended

1. Deploy empty monorepo structure to production (database + API + frontend)
2. Complete Phase 1 (Player) locally and deploy
3. Complete Phase 2 (Auth) locally and deploy
4. Complete Phase 3 (Game) locally and deploy
5. Complete Phase 4 (Spotify) locally and deploy

This sequential approach ensures each layer is stable before the next is added.

---

## Troubleshooting

### Database Connection Issues

**Problem:** `DATABASE_URL` not being recognized in production

**Solution:**
- Double-check the connection string format (should be `postgresql://...`)
- Verify the database is accessible from your deployment region
- Check firewall rules allow connections from your hosting provider

### API Not Reachable from Frontend

**Problem:** Frontend gets CORS errors when calling `/api/...`

**Solution:**
- Ensure `vercel.json` is properly configured with rewrites
- Verify the backend URL in rewrites points to your live server
- Check backend CORS headers if not using rewrites

### Spotify Token Expiration

**Problem:** Spotify API calls fail with 401 Unauthorized

**Solution:**
- Ensure token caching and refresh logic is implemented correctly
- Check that `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are set in backend environment

---

## Additional Resources

- [Render Deployment Guide](https://render.com/docs)
- [Railway Deployment Guide](https://docs.railway.app)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Lucia Auth Documentation](https://lucia-auth.com)
- [Drizzle ORM Documentation](https://orm.drizzle.team)
