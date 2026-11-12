from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel

# text[] on PostgreSQL (matches the original schema), JSON elsewhere.
_TextArray = JSON().with_variant(ARRAY(Text()), "postgresql")


class Artist(SQLModel, table=True):
    __tablename__ = "edm_artists"

    id: str = Field(primary_key=True)
    name: str
    image_url: str
    bio: str
    genres: List[str] = Field(sa_column=Column(_TextArray, nullable=False))
    followers: str
    accent: str


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


class Favorite(SQLModel, table=True):
    __tablename__ = "edm_favorites"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(default="demo-dj")
    artist_id: str = Field(foreign_key="edm_artists.id")
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class GameSession(SQLModel, table=True):
    __tablename__ = "edm_game_sessions"

    id: str = Field(primary_key=True)
    user_id: str = Field(default="demo-dj")
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
