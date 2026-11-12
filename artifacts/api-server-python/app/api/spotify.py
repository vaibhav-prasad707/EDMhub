"""Connect a user's Spotify account so the browser can stream full tracks (Web Playback SDK).

The refresh token never leaves the server: it is stored encrypted, and the browser only ever
receives short-lived access tokens from GET /spotify/token.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse

import jwt
import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.crypto import decrypt, encrypt
from app.db.models import SpotifyLink, User
from app.db.session import get_session

router = APIRouter(prefix="/spotify")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
ME_URL = "https://api.spotify.com/v1/me"
# `streaming` + the two user-read scopes are what the Web Playback SDK requires;
# the playback-state scopes let the page start a track on the in-browser device.
SCOPES = "streaming user-read-email user-read-private user-read-playback-state user-modify-playback-state"
STATE_MINUTES = 10


class AuthorizeOut(BaseModel):
    url: str


class StatusOut(BaseModel):
    connected: bool


class TokenOut(BaseModel):
    accessToken: str
    expiresIn: int


def _frontend_origin() -> str:
    parsed = urlparse(settings.SPOTIFY_REDIRECT_URI)
    return f"{parsed.scheme}://{parsed.netloc}"


def _require_configured() -> None:
    if not settings.SPOTIPY_CLIENT_ID or not settings.SPOTIPY_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Spotify is not configured on this server")


def _make_state(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=STATE_MINUTES)
    return jwt.encode({"sub": user_id, "purpose": "spotify-link", "exp": exp}, settings.JWT_SECRET, algorithm="HS256")


def _read_state(state: str) -> Optional[str]:
    try:
        payload = jwt.decode(state, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return payload.get("sub") if payload.get("purpose") == "spotify-link" else None


def _token_request(data: Dict[str, str]) -> Dict[str, Any]:
    resp = requests.post(
        TOKEN_URL, data=data, timeout=15,
        auth=(settings.SPOTIPY_CLIENT_ID or "", settings.SPOTIPY_CLIENT_SECRET or ""),
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code if resp.status_code < 500 else 502, detail="Spotify rejected the request")
    return resp.json()


def _spotify_user_id(access_token: str) -> Optional[str]:
    try:
        resp = requests.get(ME_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
        return resp.json().get("id") if resp.status_code == 200 else None
    except requests.RequestException:
        return None


@router.get("/authorize", response_model=AuthorizeOut)
def authorize(user: User = Depends(get_current_user)):
    _require_configured()
    query = urlencode({
        "client_id": settings.SPOTIPY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
        "state": _make_state(user.id),
        "show_dialog": "false",
    })
    return AuthorizeOut(url=f"{AUTH_URL}?{query}")


@router.get("/callback", include_in_schema=False)
def callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Spotify redirects the browser here. Identity comes from the signed `state`, not a cookie,
    because the redirect may land on a different host name (127.0.0.1 vs localhost)."""
    origin = _frontend_origin()
    user_id = _read_state(state) if state else None
    if error or not code or not user_id or session.get(User, user_id) is None:
        return RedirectResponse(f"{origin}/?spotify=error", status_code=302)
    try:
        tokens = _token_request({
            "grant_type": "authorization_code", "code": code, "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        })
    except HTTPException:
        return RedirectResponse(f"{origin}/?spotify=error", status_code=302)

    refresh = tokens.get("refresh_token")
    if not refresh:
        return RedirectResponse(f"{origin}/?spotify=error", status_code=302)
    link = session.get(SpotifyLink, user_id)
    spotify_user = _spotify_user_id(tokens.get("access_token", ""))
    if link is None:
        link = SpotifyLink(user_id=user_id, spotify_user_id=spotify_user, refresh_token_enc=encrypt(refresh))
    else:
        link.spotify_user_id = spotify_user
        link.refresh_token_enc = encrypt(refresh)
    session.add(link)
    session.commit()
    return RedirectResponse(f"{origin}/?spotify=connected", status_code=302)


@router.get("/status", response_model=StatusOut)
def status(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return StatusOut(connected=session.get(SpotifyLink, user.id) is not None)


@router.get("/token", response_model=TokenOut)
def access_token(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    _require_configured()
    link = session.get(SpotifyLink, user.id)
    refresh = decrypt(link.refresh_token_enc) if link else None
    if link is None or refresh is None:
        raise HTTPException(status_code=404, detail="Spotify is not connected")
    try:
        tokens = _token_request({"grant_type": "refresh_token", "refresh_token": refresh})
    except HTTPException as exc:
        if exc.status_code in (400, 401):  # revoked or expired grant: force a reconnect
            session.delete(link)
            session.commit()
            raise HTTPException(status_code=404, detail="Spotify is not connected")
        raise
    if tokens.get("refresh_token"):  # Spotify may rotate it
        link.refresh_token_enc = encrypt(tokens["refresh_token"])
        session.add(link)
        session.commit()
    return TokenOut(accessToken=tokens["access_token"], expiresIn=int(tokens.get("expires_in", 3600)))


@router.delete("/link", status_code=204)
def disconnect(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    link = session.get(SpotifyLink, user.id)
    if link:
        session.delete(link)
        session.commit()
