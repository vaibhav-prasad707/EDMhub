"""Artist/track catalog served to the frontend, read from the database."""
from collections import defaultdict
from typing import Any, Dict, List

from sqlmodel import Session, select

from app.db.models import Artist, Track
from app.lib.edm_data import GENRES


def api_track(track: Track, artist_name: str) -> Dict[str, Any]:
    return {
        "id": track.id,
        "title": track.title,
        "artistName": artist_name,
        "genre": track.genre,
        "releaseYear": track.release_year,
        "duration": track.duration,
        "color": track.color,
        "previewUrl": track.preview_url,
        "spotifyUri": track.spotify_uri,
    }


def _track_order(track: Track):
    return (not track.preview_url, track.title.lower(), track.id)


def load_artists(session: Session) -> List[Dict[str, Any]]:
    """All artists that have at least one track, in API shape (plus a private `_tracks` list).

    Once an artist has been imported from Spotify, the built-in placeholder tracks (which use
    stand-in audio) are hidden for that artist.
    """
    by_artist: Dict[str, List[Track]] = defaultdict(list)
    for track in session.exec(select(Track)).all():
        by_artist[track.artist_id].append(track)

    artists: List[Dict[str, Any]] = []
    for artist in session.exec(select(Artist)).all():
        tracks = by_artist.get(artist.id, [])
        shown = sorted([t for t in tracks if t.source == "spotify"] or tracks, key=_track_order)
        if not shown:
            continue
        api_tracks = [api_track(t, artist.name) for t in shown]
        artists.append({
            "id": artist.id,
            "name": artist.name,
            "imageUrl": artist.image_url,
            "bio": artist.bio,
            "genres": list(artist.genres),
            "followers": artist.followers,
            "accent": artist.accent,
            "topTrack": api_tracks[0],
            "_tracks": api_tracks,
        })
    # Artists whose top track is playable first, then alphabetical.
    artists.sort(key=lambda a: (not a["topTrack"]["previewUrl"], a["name"].lower()))
    return artists


def genre_list(artists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            **genre,
            "count": sum(1 for a in artists if genre["name"] in a["genres"]),
        }
        for genre in GENRES
    ]
