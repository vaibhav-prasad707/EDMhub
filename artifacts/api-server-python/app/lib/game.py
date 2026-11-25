import random
import re
from typing import List, Optional, Sequence, Tuple

from app.db.models import Artist, Track

Catalog = Sequence[Tuple[Track, Artist]]


class GameSetupError(ValueError):
    pass


def era_bounds(era: Optional[str]) -> Optional[Tuple[int, int]]:
    if not era or not era.strip():
        return None
    m = re.fullmatch(r"(\d{4})s", era.strip())
    if not m:
        raise GameSetupError(f"Unrecognised era '{era}'")
    start = int(m.group(1))
    return start, start + 9


def _playable(catalog: Catalog) -> List[Tuple[Track, Artist]]:
    playable = [(t, a) for t, a in catalog if t.preview_url]
    # Once real (Spotify-imported) tracks exist, the stand-in placeholder audio is left out.
    if any(t.source == "spotify" for t, _ in playable):
        playable = [(t, a) for t, a in playable if t.source == "spotify"]
    return playable


def playable_artists(catalog: Catalog) -> List[Tuple[Artist, int]]:
    """Artists with at least one playable track, with how many, sorted by name."""
    counts: dict = {}
    for _, a in _playable(catalog):
        art, n = counts.get(a.id, (a, 0))
        counts[a.id] = (art, n + 1)
    return sorted(counts.values(), key=lambda an: an[0].name.lower())


def build_questions(
    catalog: Catalog,
    rounds: int,
    genre: Optional[str] = None,
    era: Optional[str] = None,
    artist_id: Optional[str] = None,
    rng: Optional[random.Random] = None,
) -> List[Tuple[str, List[str]]]:
    """Return [(correct_track_id, option_track_ids)] for each round.

    Only tracks with audio are playable. Correct answers are shuffled and don't repeat until
    the pool is used up. Every option is a different artist, and distractors prefer the same
    genre so the choices stay plausible.
    """
    rng = rng or random.Random()
    playable = _playable(catalog)
    bounds = era_bounds(era)
    genre_key = genre.strip().lower() if genre and genre.strip() else None

    pool = [
        (t, a) for t, a in playable
        if (genre_key is None or t.genre.lower() == genre_key)
        and (bounds is None or bounds[0] <= t.release_year <= bounds[1])
        and (not artist_id or a.id == artist_id)
    ]
    if not pool:
        raise GameSetupError("No playable tracks match those filters")

    order: List[Tuple[Track, Artist]] = []
    while len(order) < rounds:
        cycle = pool[:]
        rng.shuffle(cycle)
        if order and len(cycle) > 1 and cycle[0][0].id == order[-1][0].id:
            cycle[0], cycle[-1] = cycle[-1], cycle[0]
        order.extend(cycle)
    order = order[:rounds]

    questions: List[Tuple[str, List[str]]] = []
    for correct, correct_artist in order:
        options = [correct]
        if artist_id:
            # One-artist quiz: every choice is a song by that artist (distinct titles), so the
            # artist name gives nothing away. Top up with similar artists if they have few songs.
            seen_titles = {correct.title.lower()}
            own = [t for t, a in playable if a.id == artist_id and t.id != correct.id]
            rng.shuffle(own)
            for t in own:
                if len(options) == 4:
                    break
                if t.title.lower() not in seen_titles:
                    options.append(t)
                    seen_titles.add(t.title.lower())
        others = [(t, a) for t, a in playable if a.id != correct_artist.id]
        rng.shuffle(others)
        others.sort(key=lambda ta: ta[0].genre != correct.genre)  # same genre first (stable)
        used_artists = {correct_artist.id} if not artist_id else set()
        for t, a in others:
            if len(options) == 4:
                break
            if a.id not in used_artists:
                options.append(t)
                used_artists.add(a.id)
        if len(options) < 2:
            raise GameSetupError("Not enough playable tracks to build a question")
        rng.shuffle(options)
        questions.append((correct.id, [t.id for t in options]))
    return questions
