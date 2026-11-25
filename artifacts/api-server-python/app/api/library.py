"""Playlists and catalog search for the Library section."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from app.api.deps import get_current_user
from app.db.models import Artist, Playlist, PlaylistTrack, Track, User
from app.db.session import get_session
from app.lib.catalog import api_track

router = APIRouter()


class TrackOut(BaseModel):
    id: str
    title: str
    artistName: str
    genre: str
    releaseYear: int
    duration: str
    color: str
    previewUrl: Optional[str] = None
    spotifyUri: Optional[str] = None


class PlaylistSummary(BaseModel):
    id: str
    name: str
    trackCount: int


class PlaylistDetail(BaseModel):
    id: str
    name: str
    tracks: List[TrackOut]


class PlaylistInput(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("name is required")
        return v


class PlaylistTrackInput(BaseModel):
    trackId: str


class SearchArtist(BaseModel):
    id: str
    name: str
    imageUrl: str
    genres: List[str]


class SearchResults(BaseModel):
    artists: List[SearchArtist]
    tracks: List[TrackOut]


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{what} not found")


def _own_playlist(session: Session, playlist_id: str, user: User) -> Playlist:
    playlist = session.get(Playlist, playlist_id)
    if playlist is None or playlist.user_id != user.id:
        raise _not_found("Playlist")
    return playlist


def _detail(session: Session, playlist: Playlist) -> PlaylistDetail:
    rows = session.exec(
        select(Track, Artist)
        .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
        .join(Artist, Artist.id == Track.artist_id)
        .where(PlaylistTrack.playlist_id == playlist.id)
        .order_by(PlaylistTrack.position, PlaylistTrack.id)
    ).all()
    return PlaylistDetail(id=playlist.id, name=playlist.name, tracks=[api_track(t, a.name) for t, a in rows])


def _like(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("/search", response_model=SearchResults)
def search_catalog(
    q: str = Query("", max_length=100),
    limit: int = Query(6, ge=1, le=20),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    term = q.strip()
    if len(term) < 1:
        return SearchResults(artists=[], tracks=[])
    pattern = _like(term.lower())

    artists = session.exec(
        select(Artist)
        .where(func.lower(Artist.name).like(pattern, escape="\\"))
        .order_by(Artist.sort_order, Artist.name)
        .limit(limit)
    ).all()

    # Placeholder (seed) tracks are hidden for artists that have real imported tracks.
    imported = select(Track.artist_id).where(Track.source == "spotify")
    track_rows = session.exec(
        select(Track, Artist)
        .join(Artist, Artist.id == Track.artist_id)
        .where(
            or_(
                func.lower(Track.title).like(pattern, escape="\\"),
                func.lower(Artist.name).like(pattern, escape="\\"),
            )
        )
        .where(or_(Track.source != "seed", col(Track.artist_id).not_in(imported)))
        .order_by(Track.preview_url.is_(None), Artist.sort_order, Track.title)
        .limit(limit)
    ).all()
    return SearchResults(
        artists=[SearchArtist(id=a.id, name=a.name, imageUrl=a.image_url, genres=list(a.genres)) for a in artists],
        tracks=[api_track(t, a.name) for t, a in track_rows],
    )


@router.get("/playlists", response_model=List[PlaylistSummary])
def list_playlists(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    counts = dict(
        session.exec(
            select(PlaylistTrack.playlist_id, func.count(PlaylistTrack.id))
            .join(Playlist, Playlist.id == PlaylistTrack.playlist_id)
            .where(Playlist.user_id == user.id)
            .group_by(PlaylistTrack.playlist_id)
        ).all()
    )
    playlists = session.exec(
        select(Playlist).where(Playlist.user_id == user.id).order_by(Playlist.created_at.desc(), Playlist.name)
    ).all()
    return [PlaylistSummary(id=p.id, name=p.name, trackCount=counts.get(p.id, 0)) for p in playlists]


@router.post("/playlists", response_model=PlaylistSummary, status_code=201)
def create_playlist(
    data: PlaylistInput, session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    playlist = Playlist(id=str(uuid.uuid4()), user_id=user.id, name=data.name)
    session.add(playlist)
    session.commit()
    return PlaylistSummary(id=playlist.id, name=playlist.name, trackCount=0)


@router.get("/playlists/{playlist_id}", response_model=PlaylistDetail)
def get_playlist(playlist_id: str, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return _detail(session, _own_playlist(session, playlist_id, user))


@router.patch("/playlists/{playlist_id}", response_model=PlaylistSummary)
def rename_playlist(
    playlist_id: str,
    data: PlaylistInput,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    playlist = _own_playlist(session, playlist_id, user)
    playlist.name = data.name
    session.add(playlist)
    session.commit()
    count = session.exec(select(func.count(PlaylistTrack.id)).where(PlaylistTrack.playlist_id == playlist.id)).one()
    return PlaylistSummary(id=playlist.id, name=playlist.name, trackCount=count)


@router.delete("/playlists/{playlist_id}", status_code=204)
def delete_playlist(playlist_id: str, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    playlist = _own_playlist(session, playlist_id, user)
    for row in session.exec(select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist.id)).all():
        session.delete(row)
    session.delete(playlist)
    session.commit()


@router.post("/playlists/{playlist_id}/tracks", response_model=PlaylistDetail)
def add_playlist_track(
    playlist_id: str,
    data: PlaylistTrackInput,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    playlist = _own_playlist(session, playlist_id, user)
    if session.get(Track, data.trackId) is None:
        raise _not_found("Track")
    already = session.exec(
        select(PlaylistTrack.id).where(PlaylistTrack.playlist_id == playlist.id, PlaylistTrack.track_id == data.trackId)
    ).first()
    if already is None:
        last = session.exec(
            select(func.max(PlaylistTrack.position)).where(PlaylistTrack.playlist_id == playlist.id)
        ).one()
        session.add(PlaylistTrack(playlist_id=playlist.id, track_id=data.trackId, position=(last or 0) + 1))
        session.commit()
    return _detail(session, playlist)


@router.delete("/playlists/{playlist_id}/tracks/{track_id}", response_model=PlaylistDetail)
def remove_playlist_track(
    playlist_id: str,
    track_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    playlist = _own_playlist(session, playlist_id, user)
    row = session.exec(
        select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist.id, PlaylistTrack.track_id == track_id)
    ).first()
    if row is not None:
        session.delete(row)
        session.commit()
    return _detail(session, playlist)
