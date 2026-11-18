from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel

# text[] on PostgreSQL (matches the original schema), JSON elsewhere.
_TextArray = JSON().with_variant(ARRAY(Text()), "postgresql")


class User(SQLModel, table=True):
    __tablename__ = "edm_users"

    id: str = Field(primary_key=True)
    username: str
    username_key: str = Field(unique=True, index=True)  # lower-cased, for uniqueness
    email: str = Field(unique=True, index=True)  # lower-cased
    password_hash: str
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class Artist(SQLModel, table=True):
    __tablename__ = "edm_artists"

    id: str = Field(primary_key=True)
    name: str
    image_url: str
    bio: str
    genres: List[str] = Field(sa_column=Column(_TextArray, nullable=False))
    followers: str
    accent: str
    spotify_id: Optional[str] = Field(default=None, unique=True, index=True)
    # Position in the curated list; the app shows artists in this order (lowest first).
    sort_order: int = Field(default=0, sa_column_kwargs={"server_default": "0"})


class Track(SQLModel, table=True):
    __tablename__ = "edm_tracks"

    id: str = Field(primary_key=True)
    title: str
    artist_id: str = Field(foreign_key="edm_artists.id")
    genre: str
    release_year: int
    duration: str
    color: str
    preview_url: Optional[str] = None
    spotify_id: Optional[str] = Field(default=None, unique=True, index=True)
    spotify_uri: Optional[str] = None
    # "seed" = built-in placeholder catalog, "spotify" = imported by the sync script
    source: str = Field(default="seed", sa_column_kwargs={"server_default": "seed"})


class Favorite(SQLModel, table=True):
    __tablename__ = "edm_favorites"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    artist_id: str = Field(foreign_key="edm_artists.id")
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class GameSession(SQLModel, table=True):
    __tablename__ = "edm_game_sessions"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    difficulty: str
    rounds: int
    current_round: int = 1
    score: int = 0
    streak: int = 0
    completed: bool = False
    started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class GameRound(SQLModel, table=True):
    __tablename__ = "edm_game_rounds"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="edm_game_sessions.id")
    question_id: str
    track_id: str = Field(foreign_key="edm_tracks.id")
    selected_option_id: Optional[str] = None
    is_correct: Optional[bool] = None
    response_time_ms: Optional[int] = None
    hints_used: int = 0


class GameQuestionRecord(SQLModel, table=True):
    """One pre-generated question per round; the answer lives only on the server."""

    __tablename__ = "edm_game_questions"
    __table_args__ = (UniqueConstraint("session_id", "round_number"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="edm_game_sessions.id", index=True)
    round_number: int
    track_id: str = Field(foreign_key="edm_tracks.id")  # the correct answer
    option_ids: List[str] = Field(sa_column=Column(JSON, nullable=False))  # track ids, display order
    asked_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))


class SpotifyLink(SQLModel, table=True):
    """A user's connected Spotify account (used for full-track playback in the browser)."""

    __tablename__ = "edm_spotify_links"

    user_id: str = Field(primary_key=True, foreign_key="edm_users.id")
    spotify_user_id: Optional[str] = None
    refresh_token_enc: str  # encrypted at rest, see app/core/crypto.py
    linked_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
