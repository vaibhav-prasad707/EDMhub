from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.core.config import settings
from app.db.models import Favorite, GameRound, GameSession
from app.db.session import get_session
from app.lib.edm_data import (
    API_ARTISTS,
    API_TRACKS,
    GENRES,
    get_artist as find_artist,
    question_for_round,
)
from app.lib.scoring import calculate_points

router = APIRouter()
USER_ID = settings.DEMO_USER_ID


# --- Response / request schemas (mirror lib/api-spec/openapi.yaml) ---

class Genre(BaseModel):
    id: str
    name: str
    count: int


class Track(BaseModel):
    id: str
    title: str
    artistName: str
    genre: str
    releaseYear: int
    duration: str
    color: str
    previewUrl: Optional[str] = None


class Artist(BaseModel):
    id: str
    name: str
    imageUrl: str
    bio: str
    genres: List[str]
    followers: str
    accent: str
    topTrack: Track
    isFavorite: Optional[bool] = None


class ArtistDetail(Artist):
    topTracks: List[Track]
    similarArtists: List[Artist]


class FavoriteState(BaseModel):
    artistId: str
    isFavorite: bool


class GameStartInput(BaseModel):
    difficulty: Literal["easy", "medium", "hard"]
    rounds: Literal[5, 10, 20]
    genre: Optional[str] = None
    era: Optional[str] = None


class GameOption(BaseModel):
    id: str
    title: str
    artistName: str


class GameQuestion(BaseModel):
    id: str
    clipLabel: str
    genre: str
    releaseYear: int
    options: List[GameOption]
    correctOptionId: str
    track: Optional[Track] = None


class GameSessionOut(BaseModel):
    id: str
    difficulty: str
    rounds: int
    currentRound: int
    score: int
    streak: int
    question: GameQuestion
    completed: bool


class GameAnswerInput(BaseModel):
    questionId: str
    optionId: str
    responseTimeMs: int
    hintsUsed: int


class GameAnswerResult(BaseModel):
    correct: bool
    correctOptionId: str
    pointsEarned: int
    totalScore: int
    streak: int
    completed: bool
    nextQuestion: Optional[GameQuestion] = None


class SystemStatus(BaseModel):
    database: str
    spotify: bool


# --- Helpers ---

def get_favorite_ids(session: Session) -> set:
    rows = session.exec(
        select(Favorite.artist_id).where(Favorite.user_id == USER_ID)
    ).all()
    return set(rows)


def with_favorite_state(artists: List[Dict[str, Any]], favorite_ids: set) -> List[Dict[str, Any]]:
    return [{**a, "isFavorite": a["id"] in favorite_ids} for a in artists]


def session_out(game: GameSession) -> GameSessionOut:
    return GameSessionOut(
        id=game.id,
        difficulty=game.difficulty,
        rounds=game.rounds,
        currentRound=game.current_round,
        score=game.score,
        streak=game.streak,
        question=question_for_round(game.current_round),
        completed=game.completed,
    )


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=404, detail=message)


# --- Endpoints ---

@router.get("/system/status", response_model=SystemStatus)
def get_system_status():
    from app.lib.spotify_client import spotify_client
    return SystemStatus(database="connected", spotify=spotify_client.is_available())


@router.get("/genres", response_model=List[Genre])
def list_genres():
    return GENRES


@router.get("/artists", response_model=List[Artist])
def list_artists(
    genre: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(12, ge=1, le=50),
    session: Session = Depends(get_session),
):
    norm_search = search.strip().lower() if search else ""
    norm_genre = genre.strip().lower() if genre else ""

    def matches(artist: Dict[str, Any]) -> bool:
        genre_ok = not norm_genre or any(g.lower() == norm_genre for g in artist["genres"])
        search_ok = (
            not norm_search
            or norm_search in artist["name"].lower()
            or norm_search in artist["bio"].lower()
        )
        return genre_ok and search_ok

    filtered = [a for a in API_ARTISTS if matches(a)]
    return with_favorite_state(filtered[:limit], get_favorite_ids(session))


@router.get("/artists/{artist_id}", response_model=ArtistDetail)
def get_artist(artist_id: str, session: Session = Depends(get_session)):
    artist = find_artist(artist_id)
    if not artist:
        raise not_found("Artist not found")

    favorite_ids = get_favorite_ids(session)
    top_tracks = [t for t in API_TRACKS if t["artistName"] == artist["name"]]
    similar = [
        c for c in API_ARTISTS
        if c["id"] != artist["id"] and any(g in artist["genres"] for g in c["genres"])
    ][:3]

    return {
        **artist,
        "isFavorite": artist["id"] in favorite_ids,
        "topTracks": top_tracks,
        "similarArtists": with_favorite_state(similar, favorite_ids),
    }


@router.get("/recommendations", response_model=List[Artist])
def get_recommendations(genres: Optional[str] = None, session: Session = Depends(get_session)):
    selected = [g.strip().lower() for g in (genres or "House,Garage").split(",") if g.strip()]
    favorite_ids = get_favorite_ids(session)
    ranked = sorted(
        API_ARTISTS,
        key=lambda a: sum(1 for g in a["genres"] if g.lower() in selected),
        reverse=True,
    )
    return with_favorite_state(ranked, favorite_ids)


@router.post("/favorites/artists/{artist_id}", response_model=FavoriteState)
def toggle_artist_favorite(artist_id: str, session: Session = Depends(get_session)):
    if not find_artist(artist_id):
        raise not_found("Artist not found")

    existing = session.exec(
        select(Favorite).where(Favorite.user_id == USER_ID, Favorite.artist_id == artist_id)
    ).first()

    if existing:
        session.delete(existing)
        is_favorite = False
    else:
        session.add(Favorite(user_id=USER_ID, artist_id=artist_id))
        is_favorite = True
    session.commit()
    return FavoriteState(artistId=artist_id, isFavorite=is_favorite)


@router.post("/game/sessions", response_model=GameSessionOut, status_code=201)
def start_game(data: GameStartInput, session: Session = Depends(get_session)):
    import uuid

    game = GameSession(
        id=str(uuid.uuid4()),
        user_id=USER_ID,
        difficulty=data.difficulty,
        rounds=data.rounds,
        current_round=1,
        score=0,
        streak=0,
        completed=False,
    )
    session.add(game)
    session.commit()
    session.refresh(game)
    return session_out(game)


@router.get("/game/sessions/{session_id}", response_model=GameSessionOut)
def get_game_session(session_id: str, session: Session = Depends(get_session)):
    game = session.get(GameSession, session_id)
    if not game:
        raise not_found("Game session not found")
    return session_out(game)


@router.post("/game/sessions/{session_id}/answers", response_model=GameAnswerResult)
def answer_game_question(
    session_id: str, data: GameAnswerInput, session: Session = Depends(get_session)
):
    game = session.get(GameSession, session_id)
    if not game:
        raise not_found("Game session not found")

    question = question_for_round(game.current_round)
    correct = data.optionId == question["correctOptionId"]
    points, next_streak = calculate_points(
        game.difficulty, game.streak, correct, data.responseTimeMs, data.hintsUsed
    )
    completed = game.current_round >= game.rounds
    next_round = game.current_round if completed else game.current_round + 1
    new_score = game.score + points

    session.add(GameRound(
        session_id=game.id,
        question_id=question["id"],
        track_id=question["track"]["id"],
        selected_option_id=data.optionId,
        is_correct=correct,
        response_time_ms=data.responseTimeMs,
        hints_used=data.hintsUsed,
    ))
    game.current_round = next_round
    game.score = new_score
    game.streak = next_streak
    game.completed = completed
    session.add(game)
    session.commit()

    return GameAnswerResult(
        correct=correct,
        correctOptionId=question["correctOptionId"],
        pointsEarned=points,
        totalScore=new_score,
        streak=next_streak,
        completed=completed,
        nextQuestion=None if completed else question_for_round(next_round),
    )


@router.get("/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    favorite_ids = get_favorite_ids(session)
    sessions = session.exec(
        select(GameSession)
        .where(GameSession.user_id == USER_ID)
        .order_by(col(GameSession.started_at))
    ).all()
    completed = [s for s in sessions if s.completed]
    extra_points = sum(s.score for s in completed)
    favorite_artists = with_favorite_state(
        [a for a in API_ARTISTS if a["id"] in favorite_ids], favorite_ids
    )
    games_played = max(12, len(sessions))

    return {
        "profile": {
            "username": "JAMIE D.",
            "initials": "JD",
            "bio": "Collecting the sounds between midnight and sunrise.",
            "memberSince": "March 2024",
        },
        "stats": {
            "gamesPlayed": games_played,
            "accuracy": 86,
            "totalPoints": 1840 + extra_points,
            "currentStreak": completed[-1].streak if completed else 7,
            "bestStreak": 18,
            "artistOfWeek": "Fred again..",
            "favoriteGenre": "House",
            "hottestTrack": "places to be",
        },
        "genreBreakdown": [
            {"genre": "House", "value": 42, "color": "#D6FF00"},
            {"genre": "Techno", "value": 24, "color": "#FF3C8B"},
            {"genre": "Garage", "value": 18, "color": "#19D3D1"},
            {"genre": "Ambient", "value": 10, "color": "#9B8CFF"},
            {"genre": "Other", "value": 6, "color": "#FF8A1F"},
        ],
        "accuracyTrend": [
            {"day": "MON", "accuracy": 71},
            {"day": "TUE", "accuracy": 79},
            {"day": "WED", "accuracy": 74},
            {"day": "THU", "accuracy": 88},
            {"day": "FRI", "accuracy": 82},
            {"day": "SAT", "accuracy": 91},
            {"day": "SUN", "accuracy": 86},
        ],
        "favoriteArtists": favorite_artists,
        "achievements": [
            {
                "id": "first-steps",
                "name": "First Steps",
                "description": "Play your first game",
                "progress": 1,
                "target": 1,
                "unlocked": True,
                "unlockedAt": "2024-03-12T21:30:00.000Z",
            },
            {
                "id": "century-club",
                "name": "Century Club",
                "description": "Score 100+ points in one session",
                "progress": 84,
                "target": 100,
                "unlocked": False,
                "unlockedAt": None,
            },
            {
                "id": "genre-master",
                "name": "House Head",
                "description": "Get 10 correct answers in House",
                "progress": 8,
                "target": 10,
                "unlocked": False,
                "unlockedAt": None,
            },
            {
                "id": "dedicated-fan",
                "name": "Dedicated Fan",
                "description": "Play 30 games total",
                "progress": min(30, games_played),
                "target": 30,
                "unlocked": False,
                "unlockedAt": None,
            },
        ],
    }


@router.get("/activity")
def list_activity():
    return [
        {"id": "activity-1", "kind": "game", "title": "Game complete",
         "detail": "82 points · 4/5 correct", "timestamp": "18 MIN AGO", "accent": "#D6FF00"},
        {"id": "activity-2", "kind": "artist", "title": "New crate find",
         "detail": "You discovered Overmono", "timestamp": "YESTERDAY", "accent": "#FF3C8B"},
        {"id": "activity-3", "kind": "achievement", "title": "Streak extended",
         "detail": "7 correct answers in a row", "timestamp": "2 DAYS AGO", "accent": "#19D3D1"},
        {"id": "activity-4", "kind": "game", "title": "Game complete",
         "detail": "105 points · 5/5 correct", "timestamp": "4 DAYS AGO", "accent": "#FF8A1F"},
        {"id": "activity-5", "kind": "artist", "title": "Favorite added",
         "detail": "Charlotte de Witte", "timestamp": "LAST WEEK", "accent": "#9B8CFF"},
    ]


@router.get("/leaderboard")
def get_leaderboard():
    def entry(rank, username, initials, score, accuracy, games, accent, me=False):
        return {
            "rank": rank, "username": username, "initials": initials, "score": score,
            "accuracy": accuracy, "games": games, "accent": accent, "isCurrentUser": me,
        }

    return {
        "entries": [
            entry(1, "MAYA K.", "MK", 4210, 94, 38, "#D6FF00"),
            entry(2, "DODGER", "DO", 3892, 91, 31, "#FF3C8B"),
            entry(3, "K-BOY", "KB", 3674, 89, 29, "#19D3D1"),
            entry(4, "JAMIE D.", "JD", 1840, 86, 12, "#FF8A1F", True),
            entry(5, "OLI M.", "OM", 1722, 84, 17, "#9B8CFF"),
        ],
        "currentUserRank": 4,
        "totalPlayers": 184,
    }
