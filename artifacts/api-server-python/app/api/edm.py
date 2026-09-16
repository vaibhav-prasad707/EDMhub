from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func, desc
from app.db.session import get_session
from app.db.models import Artist, Track, Favorite, GameSession, GameRound
from app.core.config import settings
from app.lib.scoring import calculate_points
from pydantic import BaseModel, Field


router = APIRouter()

# --- Schemas ---

class SystemStatus(BaseModel):
    database: str
    spotify: bool

class GenreResponse(BaseModel):
    id: str
    name: str
    count: int

class TrackSchema(BaseModel):
    id: str
    title: str
    artistName: str
    genre: str
    releaseYear: int
    duration: str
    color: str
    previewUrl: Optional[str] = None

class ArtistSchema(BaseModel):
    id: str
    name: str
    imageUrl: str
    bio: str
    genres: List[str]
    followers: str
    accent: str
    topTrack: TrackSchema
    isFavorite: Optional[bool] = False

class GameStartInput(BaseModel):
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    rounds: int = Field(..., ge=1, le=20)

class GameSessionResponse(BaseModel):
    id: str
    userId: str
    difficulty: str
    rounds: int
    currentRound: int
    score: int
    streak: int
    completed: bool
    startedAt: str

class GameQuestion(BaseModel):
    id: str
    clipLabel: str
    genre: str
    releaseYear: int
    options: List[Dict[str, str]]
    correctOptionId: str
    track: TrackSchema

class GameAnswerInput(BaseModel):
    sessionId: str
    optionId: str
    responseTimeMs: int
    hintsUsed: int

class GameAnswerResult(BaseModel):
    isCorrect: bool
    pointsEarned: int
    nextStreak: int
    correctOptionId: str
    track: TrackSchema
    nextQuestion: Optional[GameQuestion] = None

class DashboardStats(BaseModel):
    accuracy: float
    points: int
    genreBreakdown: List[Dict[str, Any]]
    accuracyTrend: List[Dict[str, Any]]
    favoriteArtists: List[ArtistSchema]
    achievements: List[Dict[str, Any]]

class LeaderboardEntry(BaseModel):
    rank: int
    userId: str
    userName: str
    score: int

# --- Endpoints ---

@router.get("/system/status", response_model=SystemStatus)
def get_system_status(session: Session = Depends(get_session)):
    from app.lib.spotify_client import spotify_client
    return SystemStatus(
        database="connected",
        spotify=spotify_client.is_available()
    )

@router.get("/genres", response_model=List[GenreResponse])
def get_genres(session: Session = Depends(get_session)):
    # In the original, this was static data. We'll replicate that.
    from app.lib.edm_data import GENRES
    return GENRES

@router.get("/artists", response_model=List[ArtistSchema])
def get_artists(search: Optional[str] = None, genre: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(Artist)
    if search:
        query = query.where(Artist.name.ilike(f"%{search}%"))
    if genre:
        # Artist.genres is stored as JSON list in PG
        query = query.where(Artist.genres.contains([genre]))

    artists = session.exec(query).all()

    results = []
    for artist in artists:
        # Get top track (first track in DB for that artist)
        track = session.exec(select(Track).where(Track.artist_id == artist.id).limit(1)).first()
        if not track: continue

        is_fav = session.exec(select(Favorite).where(Favorite.user_id == settings.DEMO_USER_ID, Favorite.artist_id == artist.id)).first() is not None

        results.append(ArtistSchema(
            id=artist.id,
            name=artist.name,
            imageUrl=artist.image_url,
            bio=artist.bio,
            genres=artist.genres,
            followers=artist.followers,
            accent=artist.accent,
            isFavorite=is_fav,
            topTrack=TrackSchema(
                id=track.id,
                title=track.title,
                artistName=artist.name,
                genre=track.genre,
                releaseYear=track.release_year,
                duration=track.duration,
                color=track.color,
                previewUrl=track.preview_url
            )
        ))
    return results

@router.get("/artists/{artist_id}", response_model=ArtistSchema)
def get_artist(artist_id: str, session: Session = Depends(get_session)):
    artist = session.get(Artist, artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    track = session.exec(select(Track).where(Track.artist_id == artist.id).limit(1)).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found for artist")

    is_fav = session.exec(select(Favorite).where(Favorite.user_id == settings.DEMO_USER_ID, Favorite.artist_id == artist.id)).first() is not None

    return ArtistSchema(
        id=artist.id,
        name=artist.name,
        imageUrl=artist.image_url,
        bio=artist.bio,
        genres=artist.genres,
        followers=artist.followers,
        accent=artist.accent,
        isFavorite=is_fav,
        topTrack=TrackSchema(
            id=track.id,
            title=track.title,
            artistName=artist.name,
            genre=track.genre,
            releaseYear=track.release_year,
            duration=track.duration,
            color=track.color,
            previewUrl=track.preview_url
        )
    )

@router.post("/artists/{artist_id}/favorite")
def toggle_favorite(artist_id: str, session: Session = Depends(get_session)):
    fav = session.exec(select(Favorite).where(Favorite.user_id == settings.DEMO_USER_ID, Favorite.artist_id == artist_id)).first()

    if fav:
        session.delete(fav)
        session.commit()
        return {"isFavorite": False}
    else:
        new_fav = Favorite(
            id=f"fav-{settings.DEMO_USER_ID}-{artist_id}",
            user_id=settings.DEMO_USER_ID,
            artist_id=artist_id
        )
        session.add(new_fav)
        session.commit()
        return {"isFavorite": True}

@router.get("/recommendations", response_model=List[ArtistSchema])
def get_recommendations(session: Session = Depends(get_session)):
    # Simplified recommendation: random artists that are not favorites
    favs = session.exec(select(Favorite.artist_id).where(Favorite.user_id == settings.DEMO_USER_ID)).all()
    fav_ids = [f.artist_id for f in favs]

    query = select(Artist).where(~Artist.id.in_(fav_ids))
    artists = session.exec(query).all()

    # Return top 5
    results = []
    for artist in artists[:5]:
        track = session.exec(select(Track).where(Track.artist_id == artist.id).limit(1)).first()
        if not track: continue

        results.append(ArtistSchema(
            id=artist.id,
            name=artist.name,
            imageUrl=artist.image_url,
            bio=artist.bio,
            genres=artist.genres,
            followers=artist.followers,
            accent=artist.accent,
            isFavorite=False,
            topTrack=TrackSchema(
                id=track.id,
                title=track.title,
                artistName=artist.name,
                genre=track.genre,
                releaseYear=track.release_year,
                duration=track.duration,
                color=track.color,
                previewUrl=track.preview_url
            )
        ))
    return results

# --- Game Logic ---

def generate_question(round_num: int, session: Session) -> GameQuestion:
    # Replicate the logic from questionForRound in edm-data.ts
    all_tracks = session.exec(select(Track)).all()
    if not all_tracks:
        raise HTTPException(status_code=500, detail="No tracks available")

    correct = all_tracks[(round_num - 1) % len(all_tracks)]

    # Generate 4 options
    options_indices = [(round_num - 1 + offset * 2) % len(all_tracks) for offset in range(4)]
    options_tracks = [all_tracks[i] for i in options_indices]

    if not any(t.id == correct.id for t in options_tracks):
        options_tracks[0] = correct

    return GameQuestion(
        id=f"question-{round_num}",
        clipLabel=f"CLIP 0{round_num} / 01:00",
        genre=correct.genre,
        releaseYear=correct.release_year,
        options=[{"id": t.id, "title": t.title, "artistName": t.artist.name} for t in options_tracks],
        correctOptionId=correct.id,
        track=TrackSchema(
            id=correct.id,
            title=correct.title,
            artistName=correct.artist.name,
            genre=correct.genre,
            releaseYear=correct.release_year,
            duration=correct.duration,
            color=correct.color,
            previewUrl=correct.preview_url
        )
    )

@router.post("/game/start", response_model=GameSessionResponse)
def start_game(data: GameStartInput, session: Session = Depends(get_session)):
    game_id = f"game-{settings.DEMO_USER_ID}-{datetime.utcnow().timestamp()}"
    new_session = GameSession(
        id=game_id,
        user_id=settings.DEMO_USER_ID,
        difficulty=data.difficulty,
        rounds=data.rounds,
        current_round=1,
        score=0,
        streak=0,
        completed=False,
        started_at=datetime.utcnow()
    )
    session.add(new_session)
    session.commit()

    return GameSessionResponse(
        id=new_session.id,
        userId=new_session.user_id,
        difficulty=new_session.difficulty,
        rounds=new_session.rounds,
        currentRound=new_session.current_round,
        score=new_session.score,
        streak=new_session.streak,
        completed=new_session.completed,
        startedAt=new_session.started_at.isoformat()
    )

@router.get("/game/session/{session_id}", response_model=Dict[str, Any])
def get_game_session(session_id: str, session: Session = Depends(get_session)):
    game = session.get(GameSession, session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session": GameSessionResponse(
            id=game.id,
            userId=game.user_id,
            difficulty=game.difficulty,
            rounds=game.rounds,
            currentRound=game.current_round,
            score=game.score,
            streak=game.streak,
            completed=game.completed,
            startedAt=game.started_at.isoformat()
        ),
        "question": generate_question(game.current_round, session)
    }

@router.post("/game/answer", response_model=GameAnswerResult)
def answer_game(data: GameAnswerInput, session: Session = Depends(get_session)):
    game = session.get(GameSession, data.sessionId)
    if not game:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the track for the current round
    # In a real system, we'd store the questionId in the session.
    # For this replication, we use the same logic as generate_question.
    all_tracks = session.exec(select(Track)).all()
    correct_track = all_tracks[(game.current_round - 1) % len(all_tracks)]

    points, next_streak = calculate_points(
        game,
        data.optionId,
        correct_track.id,
        data.responseTimeMs,
        data.hintsUsed
    )

    # Record the round
    round_record = GameRound(
        id=f"round-{game.id}-{game.current_round}",
        session_id=game.id,
        question_id=f"question-{game.current_round}",
        track_id=correct_track.id,
        selected_option_id=data.optionId,
        is_correct=points > 0,
        response_time_ms=data.responseTimeMs,
        hints_used=data.hintsUsed
    )
    session.add(round_record)

    # Update session
    game.score += points
    game.streak = next_streak
    game.current_round += 1
    if game.current_round > game.rounds:
        game.completed = True

    session.commit()

    # Prepare result
    result = GameAnswerResult(
        isCorrect=points > 0,
        pointsEarned=points,
        nextStreak=next_streak,
        correctOptionId=correct_track.id,
        track=TrackSchema(
            id=correct_track.id,
            title=correct_track.title,
            artistName=correct_track.artist.name,
            genre=correct_track.genre,
            releaseYear=correct_track.release_year,
            duration=correct_track.duration,
            color=correct_track.color,
            previewUrl=correct_track.preview_url
        )
    )

    if not game.completed:
        result.nextQuestion = generate_question(game.current_round, session)

    return result

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(session: Session = Depends(get_session)):
    # Mocked responses as in original
    return DashboardStats(
        accuracy=0.85,
        points=1250,
        genreBreakdown=[{"genre": "House", "count": 12}, {"genre": "Techno", "count": 8}],
        accuracyTrend=[{"date": "2024-01-01", "value": 0.7}, {"date": "2024-01-02", "value": 0.8}],
        favoriteArtists=[],
        achievements=[{"id": "first-win", "name": "First Win", "unlocked": True}]
    )

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(session: Session = Depends(get_session)):
    # Mocked responses as in original
    return [
        LeaderboardEntry(rank=1, userId="user-1", userName="DJ Legend", score=5000),
        LeaderboardEntry(rank=2, userId="user-2", userName="Bass Master", score=4200),
    ]
