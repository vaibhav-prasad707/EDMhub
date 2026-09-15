from typing import Tuple
from app.db.models import GameSession

def calculate_points(session: GameSession, option_id: str, correct_option_id: str, response_time_ms: int, hints_used: int) -> Tuple[int, int]:
    """
    Replicates the scoring logic from the TypeScript backend.
    Returns (points_earned, next_streak).
    """
    # 1. Difficulty Multiplier
    multipliers = {
        "hard": 1.5,
        "medium": 1.0,
        "easy": 0.75
    }
    multiplier = multipliers.get(session.difficulty.lower(), 1.0)

    # 2. Base Points
    is_correct = option_id == correct_option_id
    if not is_correct:
        return 0, 0

    base_points = round(10 * multiplier)

    # 3. Bonuses
    speed_bonus = 5 if response_time_ms <= 5000 else 0
    hint_bonus = 5 if hints_used == 0 else 0

    # 4. Streak
    next_streak = session.streak + 1
    streak_bonus = next_streak

    total_points = base_points + speed_bonus + hint_bonus + streak_bonus

    return total_points, next_streak
