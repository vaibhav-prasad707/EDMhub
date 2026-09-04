import { randomUUID } from "node:crypto";
import { and, eq } from "drizzle-orm";
import { Router, type IRouter } from "express";
import {
  AnswerGameQuestionBody,
  AnswerGameQuestionParams,
  AnswerGameQuestionResponse,
  GetArtistParams,
  GetArtistResponse,
  GetDashboardResponse,
  GetGameSessionParams,
  GetGameSessionResponse,
  GetLeaderboardResponse,
  GetRecommendationsQueryParams,
  GetRecommendationsResponse,
  ListActivityResponse,
  ListArtistsQueryParams,
  ListArtistsResponse,
  ListGenresResponse,
  StartGameBody,
  StartGameResponse,
  ToggleArtistFavoriteParams,
  ToggleArtistFavoriteResponse,
} from "@workspace/api-zod";
import {
  db,
  edmArtistsTable,
  edmFavoritesTable,
  edmGameRoundsTable,
  edmGameSessionsTable,
  edmTracksTable,
} from "@workspace/db";
import {
  apiArtists,
  apiTracks,
  artistSeedRows,
  genres,
  getArtist,
  questionForRound,
  trackSeedRows,
} from "../lib/edm-data";

const router: IRouter = Router();
const demoUserId = "demo-dj";
let seedPromise: Promise<void> | null = null;

async function ensureCatalogSeeded(): Promise<void> {
  if (!seedPromise) {
    seedPromise = (async () => {
      await db
        .insert(edmArtistsTable)
        .values(artistSeedRows)
        .onConflictDoNothing();
      await db
        .insert(edmTracksTable)
        .values(trackSeedRows)
        .onConflictDoNothing();
    })();
  }
  await seedPromise;
}

async function getFavoriteIds(): Promise<Set<string>> {
  const rows = await db
    .select({ artistId: edmFavoritesTable.artistId })
    .from(edmFavoritesTable)
    .where(eq(edmFavoritesTable.userId, demoUserId));
  return new Set(rows.map((row) => row.artistId));
}

function withFavoriteState(
  artists: typeof apiArtists,
  favoriteIds: Set<string>,
) {
  return artists.map((artist) => ({
    ...artist,
    isFavorite: favoriteIds.has(artist.id),
  }));
}

router.get("/genres", async (_req, res): Promise<void> => {
  res.json(ListGenresResponse.parse(genres));
});

router.get("/artists", async (req, res): Promise<void> => {
  await ensureCatalogSeeded();
  const parsed = ListArtistsQueryParams.safeParse(req.query);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const { genre, search, limit } = parsed.data;
  const normalizedSearch = search?.trim().toLowerCase();
  const normalizedGenre = genre?.trim().toLowerCase();
  const filtered = apiArtists.filter((artist) => {
    const matchesGenre =
      !normalizedGenre ||
      artist.genres.some((item) => item.toLowerCase() === normalizedGenre);
    const matchesSearch =
      !normalizedSearch ||
      artist.name.toLowerCase().includes(normalizedSearch) ||
      artist.bio.toLowerCase().includes(normalizedSearch);
    return matchesGenre && matchesSearch;
  });
  const favoriteIds = await getFavoriteIds();
  res.json(
    ListArtistsResponse.parse(withFavoriteState(filtered.slice(0, limit), favoriteIds)),
  );
});

router.get("/artists/:artistId", async (req, res): Promise<void> => {
  await ensureCatalogSeeded();
  const parsed = GetArtistParams.safeParse(req.params);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const artist = getArtist(parsed.data.artistId);
  if (!artist) {
    res.status(404).json({ error: "Artist not found" });
    return;
  }

  const favoriteIds = await getFavoriteIds();
  const topTracks = apiTracks.filter((track) =>
    track.artistName === artist.name,
  );
  const similarArtists = apiArtists
    .filter(
      (candidate) =>
        candidate.id !== artist.id &&
        candidate.genres.some((item) => artist.genres.includes(item)),
    )
    .slice(0, 3);

  res.json(
    GetArtistResponse.parse({
      ...artist,
      isFavorite: favoriteIds.has(artist.id),
      topTracks,
      similarArtists: withFavoriteState(similarArtists, favoriteIds),
    }),
  );
});

router.get("/recommendations", async (req, res): Promise<void> => {
  await ensureCatalogSeeded();
  const parsed = GetRecommendationsQueryParams.safeParse(req.query);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const selectedGenres = (parsed.data.genres ?? "House,Garage")
    .split(",")
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean);
  const favoriteIds = await getFavoriteIds();
  const matches = apiArtists
    .map((artist) => ({
      artist,
      score: artist.genres.filter((genre) =>
        selectedGenres.includes(genre.toLowerCase()),
      ).length,
    }))
    .sort((a, b) => b.score - a.score)
    .map(({ artist }) => artist);

  res.json(GetRecommendationsResponse.parse(withFavoriteState(matches, favoriteIds)));
});

router.post("/favorites/artists/:artistId", async (req, res): Promise<void> => {
  await ensureCatalogSeeded();
  const parsed = ToggleArtistFavoriteParams.safeParse(req.params);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }
  if (!getArtist(parsed.data.artistId)) {
    res.status(404).json({ error: "Artist not found" });
    return;
  }

  const existing = await db
    .select({ id: edmFavoritesTable.id })
    .from(edmFavoritesTable)
    .where(
      and(
        eq(edmFavoritesTable.userId, demoUserId),
        eq(edmFavoritesTable.artistId, parsed.data.artistId),
      ),
    )
    .limit(1);

  let isFavorite = existing.length === 0;
  if (isFavorite) {
    await db.insert(edmFavoritesTable).values({
      userId: demoUserId,
      artistId: parsed.data.artistId,
    });
  } else {
    await db
      .delete(edmFavoritesTable)
      .where(eq(edmFavoritesTable.id, existing[0].id));
  }

  res.json(
    ToggleArtistFavoriteResponse.parse({
      artistId: parsed.data.artistId,
      isFavorite,
    }),
  );
});

router.post("/game/sessions", async (req, res): Promise<void> => {
  await ensureCatalogSeeded();
  const parsed = StartGameBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const id = randomUUID();
  const difficulty = parsed.data.difficulty;
  const rounds = parsed.data.rounds;
  await db.insert(edmGameSessionsTable).values({
    id,
    userId: demoUserId,
    difficulty,
    rounds,
    currentRound: 1,
    score: 0,
    streak: 0,
    completed: false,
  });

  res.status(201).json(
    StartGameResponse.parse({
      id,
      difficulty,
      rounds,
      currentRound: 1,
      score: 0,
      streak: 0,
      question: questionForRound(1),
      completed: false,
    }),
  );
});

router.get("/game/sessions/:sessionId", async (req, res): Promise<void> => {
  const parsed = GetGameSessionParams.safeParse(req.params);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const [session] = await db
    .select()
    .from(edmGameSessionsTable)
    .where(eq(edmGameSessionsTable.id, parsed.data.sessionId))
    .limit(1);
  if (!session) {
    res.status(404).json({ error: "Game session not found" });
    return;
  }

  res.json(
    GetGameSessionResponse.parse({
      ...session,
      question: questionForRound(session.currentRound),
    }),
  );
});

router.post(
  "/game/sessions/:sessionId/answers",
  async (req, res): Promise<void> => {
    const params = AnswerGameQuestionParams.safeParse(req.params);
    if (!params.success) {
      res.status(400).json({ error: params.error.message });
      return;
    }
    const body = AnswerGameQuestionBody.safeParse(req.body);
    if (!body.success) {
      res.status(400).json({ error: body.error.message });
      return;
    }

    const [session] = await db
      .select()
      .from(edmGameSessionsTable)
      .where(eq(edmGameSessionsTable.id, params.data.sessionId))
      .limit(1);
    if (!session) {
      res.status(404).json({ error: "Game session not found" });
      return;
    }

    const question = questionForRound(session.currentRound);
    const correct = body.data.optionId === question.correctOptionId;
    const difficultyMultiplier =
      session.difficulty === "hard"
        ? 1.5
        : session.difficulty === "easy"
          ? 0.75
          : 1;
    const basePoints = correct
      ? Math.round(10 * difficultyMultiplier)
      : 0;
    const speedBonus = correct && body.data.responseTimeMs <= 5000 ? 5 : 0;
    const hintBonus = correct && body.data.hintsUsed === 0 ? 5 : 0;
    const nextStreak = correct ? session.streak + 1 : 0;
    const streakBonus = correct ? nextStreak : 0;
    const pointsEarned = basePoints + speedBonus + hintBonus + streakBonus;
    const completed = session.currentRound >= session.rounds;
    const nextRound = completed ? session.currentRound : session.currentRound + 1;

    await db.insert(edmGameRoundsTable).values({
      sessionId: session.id,
      questionId: question.id,
      trackId: question.track.id,
      selectedOptionId: body.data.optionId,
      isCorrect: correct,
      responseTimeMs: body.data.responseTimeMs,
      hintsUsed: body.data.hintsUsed,
    });
    await db
      .update(edmGameSessionsTable)
      .set({
        currentRound: nextRound,
        score: session.score + pointsEarned,
        streak: nextStreak,
        completed,
      })
      .where(eq(edmGameSessionsTable.id, session.id));

    res.json(
      AnswerGameQuestionResponse.parse({
        correct,
        correctOptionId: question.correctOptionId,
        pointsEarned,
        totalScore: session.score + pointsEarned,
        streak: nextStreak,
        completed,
        nextQuestion: completed ? null : questionForRound(nextRound),
      }),
    );
  },
);

router.get("/dashboard", async (_req, res): Promise<void> => {
  await ensureCatalogSeeded();
  const favoriteIds = await getFavoriteIds();
  const sessions = await db
    .select()
    .from(edmGameSessionsTable)
    .where(eq(edmGameSessionsTable.userId, demoUserId));
  const completedSessions = sessions.filter((session) => session.completed);
  const extraPoints = completedSessions.reduce((sum, session) => sum + session.score, 0);
  const favoriteArtists = withFavoriteState(
    apiArtists.filter((artist) => favoriteIds.has(artist.id)),
    favoriteIds,
  );

  res.json(
    GetDashboardResponse.parse({
      profile: {
        username: "JAMIE D.",
        initials: "JD",
        bio: "Collecting the sounds between midnight and sunrise.",
        memberSince: "March 2024",
      },
      stats: {
        gamesPlayed: Math.max(12, sessions.length),
        accuracy: 86,
        totalPoints: 1840 + extraPoints,
        currentStreak: completedSessions.at(-1)?.streak ?? 7,
        bestStreak: 18,
        artistOfWeek: "Fred again..",
        favoriteGenre: "House",
        hottestTrack: "places to be",
      },
      genreBreakdown: [
        { genre: "House", value: 42, color: "#D6FF00" },
        { genre: "Techno", value: 24, color: "#FF3C8B" },
        { genre: "Garage", value: 18, color: "#19D3D1" },
        { genre: "Ambient", value: 10, color: "#9B8CFF" },
        { genre: "Other", value: 6, color: "#FF8A1F" },
      ],
      accuracyTrend: [
        { day: "MON", accuracy: 71 },
        { day: "TUE", accuracy: 79 },
        { day: "WED", accuracy: 74 },
        { day: "THU", accuracy: 88 },
        { day: "FRI", accuracy: 82 },
        { day: "SAT", accuracy: 91 },
        { day: "SUN", accuracy: 86 },
      ],
      favoriteArtists,
      achievements: [
        {
          id: "first-steps",
          name: "First Steps",
          description: "Play your first game",
          progress: 1,
          target: 1,
          unlocked: true,
          unlockedAt: "2024-03-12T21:30:00.000Z",
        },
        {
          id: "century-club",
          name: "Century Club",
          description: "Score 100+ points in one session",
          progress: 84,
          target: 100,
          unlocked: false,
          unlockedAt: null,
        },
        {
          id: "genre-master",
          name: "House Head",
          description: "Get 10 correct answers in House",
          progress: 8,
          target: 10,
          unlocked: false,
          unlockedAt: null,
        },
        {
          id: "dedicated-fan",
          name: "Dedicated Fan",
          description: "Play 30 games total",
          progress: Math.min(30, Math.max(12, sessions.length)),
          target: 30,
          unlocked: false,
          unlockedAt: null,
        },
      ],
    }),
  );
});

router.get("/activity", async (_req, res): Promise<void> => {
  res.json(
    ListActivityResponse.parse([
      {
        id: "activity-1",
        kind: "game",
        title: "Game complete",
        detail: "82 points · 4/5 correct",
        timestamp: "18 MIN AGO",
        accent: "#D6FF00",
      },
      {
        id: "activity-2",
        kind: "artist",
        title: "New crate find",
        detail: "You discovered Overmono",
        timestamp: "YESTERDAY",
        accent: "#FF3C8B",
      },
      {
        id: "activity-3",
        kind: "achievement",
        title: "Streak extended",
        detail: "7 correct answers in a row",
        timestamp: "2 DAYS AGO",
        accent: "#19D3D1",
      },
      {
        id: "activity-4",
        kind: "game",
        title: "Game complete",
        detail: "105 points · 5/5 correct",
        timestamp: "4 DAYS AGO",
        accent: "#FF8A1F",
      },
      {
        id: "activity-5",
        kind: "artist",
        title: "Favorite added",
        detail: "Charlotte de Witte",
        timestamp: "LAST WEEK",
        accent: "#9B8CFF",
      },
    ]),
  );
});

router.get("/leaderboard", async (_req, res): Promise<void> => {
  res.json(
    GetLeaderboardResponse.parse({
      entries: [
        {
          rank: 1,
          username: "MAYA K.",
          initials: "MK",
          score: 4210,
          accuracy: 94,
          games: 38,
          accent: "#D6FF00",
          isCurrentUser: false,
        },
        {
          rank: 2,
          username: "DODGER",
          initials: "DO",
          score: 3892,
          accuracy: 91,
          games: 31,
          accent: "#FF3C8B",
          isCurrentUser: false,
        },
        {
          rank: 3,
          username: "K-BOY",
          initials: "KB",
          score: 3674,
          accuracy: 89,
          games: 29,
          accent: "#19D3D1",
          isCurrentUser: false,
        },
        {
          rank: 4,
          username: "JAMIE D.",
          initials: "JD",
          score: 1840,
          accuracy: 86,
          games: 12,
          accent: "#FF8A1F",
          isCurrentUser: true,
        },
        {
          rank: 5,
          username: "OLI M.",
          initials: "OM",
          score: 1722,
          accuracy: 84,
          games: 17,
          accent: "#9B8CFF",
          isCurrentUser: false,
        },
      ],
      currentUserRank: 4,
      totalPlayers: 184,
    }),
  );
});

export default router;