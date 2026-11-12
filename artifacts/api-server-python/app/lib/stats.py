"""Per-user stats, activity and leaderboard computed from stored game rounds."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import case, func
from sqlmodel import Session, col, select

from app.db.models import Favorite, GameRound, GameSession, Track, User
from app.lib.edm_data import API_ARTISTS, get_artist
from app.lib.names import initials_for

PALETTE = ["#D6FF00", "#FF3C8B", "#19D3D1", "#9B8CFF", "#FF8A1F"]
DAY_LABELS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def aware(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    # Postgres hands back the session's timezone; normalise to UTC so day bucketing is consistent.
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def iso(dt: Optional[datetime]) -> str:
    return aware(dt).isoformat()


def pct(correct: int, total: int) -> int:
    return round(100 * correct / total) if total else 0


def _streaks(flags: List[bool]):
    best = run = 0
    for ok in flags:
        run = run + 1 if ok else 0
        best = max(best, run)
    return best, run  # best run, trailing (current) run


def dashboard_stats(session: Session, user: User, favorite_ids: set) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    sessions = session.exec(
        select(GameSession).where(GameSession.user_id == user.id).order_by(col(GameSession.started_at))
    ).all()
    rows = session.exec(
        select(GameRound, GameSession, Track)
        .join(GameSession, GameRound.session_id == GameSession.id)
        .join(Track, GameRound.track_id == Track.id)
        .where(GameSession.user_id == user.id)
        .order_by(col(GameRound.id))
    ).all()

    completed = [s for s in sessions if s.completed]
    flags = [bool(r.is_correct) for r, _, _ in rows]
    best_streak, current_streak = _streaks(flags)

    # Accuracy over the last 30 days
    cutoff = now - timedelta(days=30)
    recent = [bool(r.is_correct) for r, s, _ in rows if aware(s.started_at) >= cutoff]
    accuracy = pct(sum(recent), len(recent))

    # Genres: share of rounds played per genre (top 4, rest grouped)
    genre_counts = Counter(t.genre for _, _, t in rows)
    breakdown: List[Dict[str, Any]] = []
    total_rounds = sum(genre_counts.values())
    if total_rounds:
        top = genre_counts.most_common(4)
        for i, (genre, count) in enumerate(top):
            breakdown.append({"genre": genre, "value": pct(count, total_rounds), "color": PALETTE[i]})
        rest = total_rounds - sum(c for _, c in top)
        if rest:
            breakdown.append({"genre": "Other", "value": pct(rest, total_rounds), "color": PALETTE[4]})

    # Accuracy per day for the last 7 days (days without games show 0)
    per_day: Dict[Any, List[bool]] = {}
    for r, s, _ in rows:
        per_day.setdefault(aware(s.started_at).date(), []).append(bool(r.is_correct))
    trend = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        day_flags = per_day.get(day, [])
        trend.append({"day": DAY_LABELS[day.weekday()], "accuracy": pct(sum(day_flags), len(day_flags))})

    correct_genres = Counter(t.genre for r, _, t in rows if r.is_correct)
    favorite_genre = correct_genres.most_common(1)[0][0] if correct_genres else "—"
    track_counts = Counter(t.title for _, _, t in rows)
    hottest = track_counts.most_common(1)[0][0] if track_counts else "—"

    week = now.isocalendar()[1]
    return {
        "stats": {
            "gamesPlayed": len(completed),
            "accuracy": accuracy,
            "totalPoints": sum(s.score for s in sessions),
            "currentStreak": current_streak,
            "bestStreak": best_streak,
            "artistOfWeek": API_ARTISTS[week % len(API_ARTISTS)]["name"],
            "favoriteGenre": favorite_genre,
            "hottestTrack": hottest,
        },
        "genreBreakdown": breakdown,
        "accuracyTrend": trend,
        "achievements": _achievements(sessions, completed, rows),
    }


def _achievements(sessions, completed, rows) -> List[Dict[str, Any]]:
    def item(id_, name, description, progress, target, unlocked_at):
        return {
            "id": id_, "name": name, "description": description,
            "progress": min(progress, target), "target": target,
            "unlocked": progress >= target,
            "unlockedAt": iso(unlocked_at) if progress >= target and unlocked_at else None,
        }

    best_session = max(sessions, key=lambda s: s.score, default=None)
    best_score = best_session.score if best_session else 0

    house_times = [s.started_at for r, s, t in rows if r.is_correct and t.genre == "House"]
    return [
        item("first-steps", "First Steps", "Play your first game",
             len(completed), 1, completed[0].started_at if completed else None),
        item("century-club", "Century Club", "Score 100+ points in one session",
             best_score, 100, best_session.started_at if best_session else None),
        item("genre-master", "House Head", "Get 10 correct answers in House",
             len(house_times), 10, house_times[9] if len(house_times) >= 10 else None),
        item("dedicated-fan", "Dedicated Fan", "Play 30 games total",
             len(completed), 30, completed[29].started_at if len(completed) >= 30 else None),
    ]


def recent_activity(session: Session, user: User, limit: int = 10) -> List[Dict[str, Any]]:
    events = []
    rows = session.exec(
        select(GameSession, func.count(GameRound.id), func.coalesce(func.sum(case((GameRound.is_correct, 1), else_=0)), 0))
        .join(GameRound, GameRound.session_id == GameSession.id, isouter=True)
        .where(GameSession.user_id == user.id, GameSession.completed == True)  # noqa: E712
        .group_by(GameSession.id)
    ).all()
    for game, answered, correct in rows:
        events.append({
            "id": f"game-{game.id}", "kind": "game", "title": "Game complete",
            "detail": f"{game.score} points · {int(correct)}/{answered} correct",
            "when": aware(game.started_at), "accent": PALETTE[0],
        })
    for fav in session.exec(select(Favorite).where(Favorite.user_id == user.id)).all():
        artist = get_artist(fav.artist_id)
        events.append({
            "id": f"favorite-{fav.id}", "kind": "artist", "title": "Favorite added",
            "detail": artist["name"] if artist else fav.artist_id,
            "when": aware(fav.created_at), "accent": PALETTE[3],
        })
    events.sort(key=lambda e: e["when"], reverse=True)
    return [
        {"id": e["id"], "kind": e["kind"], "title": e["title"], "detail": e["detail"],
         "timestamp": e["when"].isoformat(), "accent": e["accent"]}
        for e in events[:limit]
    ]


def leaderboard(session: Session, user: User, top_n: int = 10) -> Dict[str, Any]:
    users = session.exec(select(User)).all()
    score_rows = session.exec(
        select(
            GameSession.user_id,
            func.coalesce(func.sum(GameSession.score), 0),
            func.coalesce(func.sum(case((GameSession.completed, 1), else_=0)), 0),
        ).group_by(GameSession.user_id)
    ).all()
    acc_rows = session.exec(
        select(
            GameSession.user_id,
            func.count(GameRound.id),
            func.coalesce(func.sum(case((GameRound.is_correct, 1), else_=0)), 0),
        )
        .join(GameSession, GameRound.session_id == GameSession.id)
        .group_by(GameSession.user_id)
    ).all()
    scores = {uid: (int(score), int(games)) for uid, score, games in score_rows}
    accuracy = {uid: pct(int(correct), int(total)) for uid, total, correct in acc_rows}

    def sort_key(u: User):
        score, games = scores.get(u.id, (0, 0))
        return (-score, -games, aware(u.created_at), u.id)

    ranked = sorted(users, key=sort_key)
    entries = []
    for rank, u in enumerate(ranked, start=1):
        if rank > top_n and u.id != user.id:
            continue
        score, games = scores.get(u.id, (0, 0))
        entries.append({
            "rank": rank, "username": u.username.upper(), "initials": initials_for(u.username),
            "score": score, "accuracy": accuracy.get(u.id, 0), "games": games,
            "accent": PALETTE[(rank - 1) % len(PALETTE)], "isCurrentUser": u.id == user.id,
        })
    my_rank = next((i for i, u in enumerate(ranked, start=1) if u.id == user.id), len(ranked))
    return {"entries": entries, "currentUserRank": my_rank, "totalPlayers": len(ranked)}
