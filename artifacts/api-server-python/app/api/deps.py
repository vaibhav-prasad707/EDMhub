from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from app.core.security import COOKIE_NAME, read_session_token
from app.db.models import User
from app.db.session import get_session


def get_optional_user(request: Request, session: Session = Depends(get_session)) -> Optional[User]:
    token = request.cookies.get(COOKIE_NAME)
    user_id = read_session_token(token) if token else None
    return session.get(User, user_id) if user_id else None


def get_current_user(user: Optional[User] = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user
