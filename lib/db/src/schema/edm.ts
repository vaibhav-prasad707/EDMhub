import {
  boolean,
  integer,
  pgTable,
  serial,
  text,
  timestamp,
} from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod/v4";

export const edmArtistsTable = pgTable("edm_artists", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  imageUrl: text("image_url").notNull(),
  bio: text("bio").notNull(),
  genres: text("genres").array().notNull(),
  followers: text("followers").notNull(),
  accent: text("accent").notNull(),
});

export const edmTracksTable = pgTable("edm_tracks", {
  id: text("id").primaryKey(),
  title: text("title").notNull(),
  artistId: text("artist_id")
    .notNull()
    .references(() => edmArtistsTable.id),
  genre: text("genre").notNull(),
  releaseYear: integer("release_year").notNull(),
  duration: text("duration").notNull(),
  color: text("color").notNull(),
  previewUrl: text("preview_url"),
});

export const edmFavoritesTable = pgTable("edm_favorites", {
  id: serial("id").primaryKey(),
  userId: text("user_id").notNull().default("demo-dj"),
  artistId: text("artist_id")
    .notNull()
    .references(() => edmArtistsTable.id),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const edmGameSessionsTable = pgTable("edm_game_sessions", {
  id: text("id").primaryKey(),
  userId: text("user_id").notNull().default("demo-dj"),
  difficulty: text("difficulty").notNull(),
  rounds: integer("rounds").notNull(),
  currentRound: integer("current_round").notNull().default(1),
  score: integer("score").notNull().default(0),
  streak: integer("streak").notNull().default(0),
  completed: boolean("completed").notNull().default(false),
  startedAt: timestamp("started_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const edmGameRoundsTable = pgTable("edm_game_rounds", {
  id: serial("id").primaryKey(),
  sessionId: text("session_id")
    .notNull()
    .references(() => edmGameSessionsTable.id),
  questionId: text("question_id").notNull(),
  trackId: text("track_id")
    .notNull()
    .references(() => edmTracksTable.id),
  selectedOptionId: text("selected_option_id"),
  isCorrect: boolean("is_correct"),
  responseTimeMs: integer("response_time_ms"),
  hintsUsed: integer("hints_used").notNull().default(0),
});

export const insertEdmArtistSchema = createInsertSchema(edmArtistsTable);
export const insertEdmTrackSchema = createInsertSchema(edmTracksTable);
export type EdmArtist = typeof edmArtistsTable.$inferSelect;
export type EdmTrack = typeof edmTracksTable.$inferSelect;