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


def build_questions(
    catalog: Catalog,
    rounds: int,
    genre: Optional[str] = None,
    era: Optional[str] = None,
    rng: Optional[random.Random] = None,
) -> List[Tuple[str, List[str]]]:
    """Return [(correct_track_id, option_track_ids)] for each round.

    Only tracks with audio are playable. Correct answers are shuffled and don't repeat until
    the pool is used up. Every option is a different artist, and distractors prefer the same
    genre so the choices stay plausible.
    """
    rng = rng or random.Random()
    playable = [(t, a) for t, a in catalog if t.preview_url]
    # Once real (Spotify-imported) tracks exist, the stand-in placeholder audio is left out.
    if any(t.source == "spotify" for t, _ in playable):
        playable = [(t, a) for t, a in playable if t.source == "spotify"]
    bounds = era_bounds(era)
    genre_key = genre.strip().lower() if genre and genre.strip() else None

    pool = [
        (t, a) for t, a in playable
        if (genre_key is None or t.genre.lower() == genre_key)
        and (bounds is None or bounds[0] <= t.release_year <= bounds[1])
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
        others = [(t, a) for t, a in playable if a.id != correct_artist.id]
        rng.shuffle(others)
        others.sort(key=lambda ta: ta[0].genre != correct.genre)  # same genre first (stable)
        options = [correct]
        used_artists = {correct_artist.id}
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
