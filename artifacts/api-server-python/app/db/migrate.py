"""Minimal idempotent schema upgrades for tables that already exist.

SQLModel's create_all() creates missing tables but never alters existing ones, so columns added
after a table was first created are applied here. Postgres only; fresh databases (and SQLite in
tests) already get the columns from create_all().
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine

STATEMENTS = [
    "ALTER TABLE edm_artists ADD COLUMN IF NOT EXISTS spotify_id VARCHAR",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_edm_artists_spotify_id ON edm_artists (spotify_id)",
    "ALTER TABLE edm_tracks ADD COLUMN IF NOT EXISTS spotify_id VARCHAR",
    "ALTER TABLE edm_tracks ADD COLUMN IF NOT EXISTS spotify_uri VARCHAR",
    "ALTER TABLE edm_tracks ADD COLUMN IF NOT EXISTS source VARCHAR NOT NULL DEFAULT 'seed'",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_edm_tracks_spotify_id ON edm_tracks (spotify_id)",
]


def apply_migrations(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as conn:
        for statement in STATEMENTS:
            conn.execute(text(statement))
