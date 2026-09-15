from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship, Column, JSON

class Artist(SQLModel, table=True):
    __tablename__ = "edm_artists"

    id: str = Field(primary_key=True)
    name: str
    image_url: str = Field(alias="imageUrl")
    bio: str
    genres: List[str] = Field(default=[], sa_column=Column(JSON))
    followers: str
    accent: str

    tracks: List["Track"] = Relationship(back_populates="artist")
    favorites: List["Favorite"] = Relationship(back_populates="artist")

class Track(SQLModel, table=True):
    __tablename__ = "edm_tracks"

    id: str = Field(primary_key=True)
    title: str
    artist_id: str = Field(foreign_key="edm_artists.id", alias="artistId")
    genre: str
    release_year: int = Field(alias="releaseYear")
    duration: str
    color: str
    preview_url: Optional[str] = Field(default=None, alias="previewUrl")

    artist: Artist = Relationship(back_populates="tracks")
    game_rounds: List["GameRound"] = Relationship(back_populates="track")

class Favorite(SQLModel, table=True):
    __tablename__ = "edm_favorites"

    id: str = Field(primary_key=True)
    user_id: str = Field(alias="userId")
    artist_id: str = Field(foreign_key="edm_artists.id", alias="artistId")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")

    artist: Artist = Relationship(back_populates="favorites")

class GameSession(SQLModel, table=True):
    __tablename__ = "edm_game_sessions"

    id: str = Field(primary_key=True)
    user_id: str = Field(alias="userId")
    difficulty: str
    rounds: int
    current_round: int = Field(alias="currentRound")
    score: int
    streak: int
    completed: bool
    started_at: datetime = Field(default_factory=datetime.utcnow, alias="startedAt")

    rounds_played: List["GameRound"] = Relationship(back_populates="session")

class GameRound(SQLModel, table=True):
    __tablename__ = "edm_game_rounds"

    id: str = Field(primary_key=True)
    session_id: str = Field(foreign_key="edm_game_sessions.id", alias="sessionId")
    question_id: str = Field(alias="questionId")
    track_id: str = Field(foreign_key="edm_tracks.id", alias="trackId")
    selected_option_id: Optional[str] = Field(default=None, alias="selectedOptionId")
    is_correct: bool = Field(alias="isCorrect")
    response_time_ms: int = Field(alias="responseTimeMs")
    hints_used: int = Field(alias="hintsUsed")

    session: GameSession = Relationship(back_populates="rounds_played")
    track: Track = Relationship(back_populates="game_rounds")
