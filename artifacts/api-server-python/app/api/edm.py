import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.api.deps import get_current_user, get_optional_user
from app.db.models import Artist as DbArtist
from app.db.models import Favorite, GameQuestionRecord, GameRound, GameSession
from app.db.models import Track as DbTrack
from app.db.models import User
from app.api.auth import user_out
from app.db.session import get_session
from app.lib.catalog import genre_list, load_artists
from app.lib.game import GameSetupError, build_questions
from app.lib.scoring import calculate_points
from app.lib.stats import aware, dashboard_stats, leaderboard, recent_activity

router = APIRouter()


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
    spotifyUri: Optional[str] = None


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
    clipUrl: str


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

def get_favorite_ids(session: Session, user: Optional[User]) -> set:
    if user is None:
        return set()
    rows = session.exec(
        select(Favorite.artist_id).where(Favorite.user_id == user.id)
    ).all()
    return set(rows)


def with_favorite_state(artists: List[Dict[str, Any]], favorite_ids: set) -> List[Dict[str, Any]]:
    return [{**a, "isFavorite": a["id"] in favorite_ids} for a in artists]


def load_catalog(session: Session) -> List[Tuple[DbTrack, DbArtist]]:
    return list(session.exec(select(DbTrack, DbArtist).join(DbArtist, DbTrack.artist_id == DbArtist.id)).all())


def question_out(session: Session, game: GameSession, record: GameQuestionRecord) -> GameQuestion:
    ids = set(record.option_ids) | {record.track_id}
    by_id = {
        t.id: (t, a)
        for t, a in session.exec(
            select(DbTrack, DbArtist).join(DbArtist, DbTrack.artist_id == DbArtist.id).where(col(DbTrack.id).in_(ids))
        ).all()
    }
    correct, _ = by_id[record.track_id]
    return GameQuestion(
        id=f"question-{record.round_number}",
        clipLabel=f"CLIP {record.round_number:02d} / {game.rounds:02d}",
        genre=correct.genre,
        releaseYear=correct.release_year,
        options=[
            GameOption(id=by_id[tid][0].id, title=by_id[tid][0].title, artistName=by_id[tid][1].name)
            for tid in record.option_ids
        ],
        clipUrl=correct.preview_url or "",
    )


def current_question(session: Session, game: GameSession) -> GameQuestionRecord:
    record = session.exec(
        select(GameQuestionRecord).where(
            GameQuestionRecord.session_id == game.id,
            GameQuestionRecord.round_number == game.current_round,
        )
    ).first()
    if record is None:
        raise not_found("Game session not found")
    return record


def session_out(session: Session, game: GameSession) -> GameSessionOut:
    return GameSessionOut(
        id=game.id,
        difficulty=game.difficulty,
        rounds=game.rounds,
        currentRound=game.current_round,
        score=game.score,
        streak=game.streak,
        question=question_out(session, game, current_question(session, game)),
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
def list_genres(session: Session = Depends(get_session)):
    return genre_list(load_artists(session))


@router.get("/artists", response_model=List[Artist])
def list_artists(
    genre: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(12, ge=1, le=50),
    session: Session = Depends(get_session),
    user: Optional[User] = Depends(get_optional_user),
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

    filtered = [a for a in load_artists(session) if matches(a)]
    return with_favorite_state(filtered[:limit], get_favorite_ids(session, user))


@router.get("/artists/{artist_id}", response_model=ArtistDetail)
def get_artist(
    artist_id: str,
    session: Session = Depends(get_session),
    user: Optional[User] = Depends(get_optional_user),
):
    artists = load_artists(session)
    artist = next((a for a in artists if a["id"] == artist_id), None)
    if not artist:
        raise not_found("Artist not found")

    favorite_ids = get_favorite_ids(session, user)
    top_tracks = artist["_tracks"]
    similar = [
        c for c in artists
        if c["id"] != artist["id"] and any(g in artist["genres"] for g in c["genres"])
    ][:3]

    return {
        **artist,
        "isFavorite": artist["id"] in favorite_ids,
        "topTracks": top_tracks,
        "similarArtists": with_favorite_state(similar, favorite_ids),
    }


@router.get("/recommendations", response_model=List[Artist])
def get_recommendations(
    genres: Optional[str] = None,
    session: Session = Depends(get_session),
    user: Optional[User] = Depends(get_optional_user),
):
    selected = [g.strip().lower() for g in (genres or "House,Garage").split(",") if g.strip()]
    favorite_ids = get_favorite_ids(session, user)
    ranked = sorted(
        load_artists(session),
        key=lambda a: sum(1 for g in a["genres"] if g.lower() in selected),
        reverse=True,
    )
    return with_favorite_state(ranked, favorite_ids)


@router.post("/favorites/artists/{artist_id}", response_model=FavoriteState)
def toggle_artist_favorite(
    artist_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if session.get(DbArtist, artist_id) is None:
        raise not_found("Artist not found")

    existing = session.exec(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.artist_id == artist_id)
    ).first()

    if existing:
        session.delete(existing)
        is_favorite = False
    else:
        session.add(Favorite(user_id=user.id, artist_id=artist_id))
        is_favorite = True
    session.commit()
    return FavoriteState(artistId=artist_id, isFavorite=is_favorite)


@router.post("/game/sessions", response_model=GameSessionOut, status_code=201)
def start_game(
    data: GameStartInput,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        plan = build_questions(load_catalog(session), data.rounds, data.genre, data.era)
    except GameSetupError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    now = datetime.now(timezone.utc)
    game = GameSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        difficulty=data.difficulty,
        rounds=data.rounds,
        current_round=1,
        score=0,
        streak=0,
        completed=False,
    )
    session.add(game)
    session.flush()
    for n, (track_id, option_ids) in enumerate(plan, start=1):
        session.add(GameQuestionRecord(
            session_id=game.id,
            round_number=n,
            track_id=track_id,
            option_ids=option_ids,
            asked_at=now if n == 1 else None,
        ))
    session.commit()
    session.refresh(game)
    return session_out(session, game)


@router.get("/game/sessions/{session_id}", response_model=GameSessionOut)
def get_game_session(
    session_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    game = session.get(GameSession, session_id)
    if not game or game.user_id != user.id:
        raise not_found("Game session not found")
    return session_out(session, game)


@router.post("/game/sessions/{session_id}/answers", response_model=GameAnswerResult)
def answer_game_question(
    session_id: str,
    data: GameAnswerInput,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    # Lock the session row so a double-submitted answer can't be scored twice.
    game = session.exec(
        select(GameSession).where(GameSession.id == session_id).with_for_update()
    ).first()
    if not game or game.user_id != user.id:
        raise not_found("Game session not found")
    if game.completed:
        raise HTTPException(status_code=409, detail="Game already completed")

    record = current_question(session, game)
    if data.questionId != f"question-{record.round_number}":
        raise HTTPException(status_code=409, detail="That question is no longer active")
    if data.optionId not in record.option_ids:
        raise HTTPException(status_code=400, detail="Unknown answer option")

    now = datetime.now(timezone.utc)
    # Timed on the server from when the question was served, not taken from the client.
    response_ms = max(0, int((now - aware(record.asked_at)).total_seconds() * 1000))
    hints_used = max(0, data.hintsUsed)

    correct = data.optionId == record.track_id
    points, next_streak = calculate_points(
        game.difficulty, game.streak, correct, response_ms, hints_used
    )
    completed = game.current_round >= game.rounds
    new_score = game.score + points

    session.add(GameRound(
        session_id=game.id,
        question_id=f"question-{record.round_number}",
        track_id=record.track_id,
        selected_option_id=data.optionId,
        is_correct=correct,
        response_time_ms=response_ms,
        hints_used=hints_used,
    ))
    game.score = new_score
    game.streak = next_streak
    game.completed = completed
    next_question = None
    if not completed:
        game.current_round += 1
        following = current_question(session, game)
        following.asked_at = now
        session.add(following)
        next_question = question_out(session, game, following)
    session.add(game)
    session.commit()

    return GameAnswerResult(
        correct=correct,
        correctOptionId=record.track_id,
        pointsEarned=points,
        totalScore=new_score,
        streak=next_streak,
        completed=completed,
        nextQuestion=next_question,
    )


@router.get("/dashboard")
def get_dashboard(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    profile = user_out(user)
    favorite_ids = get_favorite_ids(session, user)
    artists = load_artists(session)
    stats = dashboard_stats(session, user, artists)
    return {
        "profile": {
            "username": profile.username.upper(),
            "initials": profile.initials,
            "bio": "Collecting the sounds between midnight and sunrise.",
            "memberSince": profile.memberSince,
        },
        **stats,
        "favoriteArtists": with_favorite_state(
            [a for a in artists if a["id"] in favorite_ids], favorite_ids
        ),
    }


@router.get("/activity")
def list_activity(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return recent_activity(session, user)


@router.get("/leaderboard")
def get_leaderboard(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return leaderboard(session, user)
