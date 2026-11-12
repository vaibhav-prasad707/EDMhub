import math
from typing import Tuple

DIFFICULTY_MULTIPLIERS = {"hard": 1.5, "medium": 1.0, "easy": 0.75}


def _js_round(x: float) -> int:
    # Math.round semantics (half rounds up), not Python's banker's rounding.
    return int(math.floor(x + 0.5))


def calculate_points(
    difficulty: str,
    current_streak: int,
    correct: bool,
    response_time_ms: int,
    hints_used: int,
) -> Tuple[int, int]:
    """Return (points_earned, next_streak)."""
    if not correct:
        return 0, 0

    multiplier = DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)
    base_points = _js_round(10 * multiplier)
    speed_bonus = 5 if response_time_ms <= 5000 else 0
    hint_bonus = 5 if hints_used == 0 else 0
    next_streak = current_streak + 1
    return base_points + speed_bonus + hint_bonus + next_streak, next_streak
