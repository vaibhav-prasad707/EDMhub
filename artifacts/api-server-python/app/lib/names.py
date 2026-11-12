import re


def initials_for(username: str) -> str:
    parts = [p for p in re.split(r"[\s._\-]+", username) if p]
    return ((parts[0][0] + parts[1][0]) if len(parts) > 1 else username[:2]).upper()
