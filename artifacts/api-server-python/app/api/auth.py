import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    COOKIE_NAME,
    create_session_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.db.session import get_session
from app.lib.names import initials_for

router = APIRouter(prefix="/auth")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\- ]+$")


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    initials: str
    memberSince: str


class SignupInput(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or not _USERNAME_RE.match(v):
            raise ValueError("username may only contain letters, numbers, spaces, '.', '_' and '-'")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v


class LoginInput(BaseModel):
    email: str
    password: str = Field(max_length=128)


def user_out(user: User) -> UserOut:
    created = user.created_at
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        initials=initials_for(user.username),
        memberSince=created.strftime("%B %Y") if created else "",
    )


def set_session_cookie(response: Response, user_id: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(user_id),
        max_age=settings.SESSION_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(data: SignupInput, response: Response, session: Session = Depends(get_session)):
    taken = session.exec(
        select(User).where(
            (User.email == data.email) | (User.username_key == data.username.lower())
        )
    ).first()
    if taken:
        raise HTTPException(status_code=409, detail="Username or email already taken")

    user = User(
        id=str(uuid.uuid4()),
        username=data.username,
        username_key=data.username.lower(),
        email=data.email,
        password_hash=hash_password(data.password),
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:  # lost a race with a concurrent signup
        session.rollback()
        raise HTTPException(status_code=409, detail="Username or email already taken")
    session.refresh(user)
    set_session_cookie(response, user.id)
    return user_out(user)


@router.post("/login", response_model=UserOut)
def login(data: LoginInput, response: Response, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email.strip().lower())).first()
    if not verify_password(data.password, user.password_hash if user else None):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_session_cookie(response, user.id)
    return user_out(user)


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", samesite="lax", secure=settings.COOKIE_SECURE, httponly=True)
    response.status_code = 204
    return response


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)
