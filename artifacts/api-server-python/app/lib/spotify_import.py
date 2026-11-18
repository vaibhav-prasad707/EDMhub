"""Import the curated artist list from Spotify into the database, with iTunes preview clips."""
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from sqlmodel import Session, select

from app.db.models import Artist, Track
from app.lib.edm_data import IMAGE_URLS
from app.lib.text import fold, slugify, title_key

ACCENTS = ["#D6FF00", "#FF3C8B", "#19D3D1", "#FF8A1F", "#9B8CFF"]


@dataclass
class SyncReport:
    artists_added: int = 0
    artists_updated: int = 0
    artists_skipped: List[str] = field(default_factory=list)
    tracks_added: int = 0
    tracks_updated: int = 0
    previews_matched: int = 0
    tracks_without_preview: int = 0
    artists_unchanged_network: int = 0  # already imported: only genres/order refreshed
    ambiguous: List[str] = field(default_factory=list)
    no_previews: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"artists: +{self.artists_added} new, {self.artists_updated} updated, "
            f"{len(self.artists_skipped)} skipped | tracks: +{self.tracks_added} new, "
            f"{self.tracks_updated} updated | previews: {self.previews_matched} matched, "
            f"{self.tracks_without_preview} without | "
            f"{self.artists_unchanged_network} already imported (not re-fetched)"
        )


def _pick(values: Sequence[str], seed: str) -> str:
    return values[int(hashlib.sha1(seed.encode()).hexdigest(), 16) % len(values)]


def format_duration(ms: int) -> str:
    seconds = round(ms / 1000)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def release_year(album: Dict[str, Any]) -> int:
    try:
        return int(str(album.get("release_date", ""))[:4])
    except ValueError:
        return 0


def match_preview(artist_name: str, track_name: str, itunes_songs: List[Dict[str, Any]]) -> Optional[str]:
    """Preview URL for a track, only when both the artist and the title agree."""
    wanted_artist = fold(artist_name)
    wanted_title = title_key(track_name)
    if not wanted_title:
        return None
    for song in itunes_songs:
        credited = fold(song.get("artistName", ""))
        if wanted_artist not in credited:
            continue
        if title_key(song.get("trackName", "")) == wanted_title:
            return song["previewUrl"]
    return None


def sync_catalog(
    session: Session,
    spotify: Any,
    itunes: Any,
    curated: Sequence[Tuple[str, List[str]]],
    per_artist: int = 6,
    only_genre: Optional[str] = None,
    previews: bool = True,
    refresh: bool = False,
    log: Callable[[str], None] = lambda _: None,
) -> SyncReport:
    """Upsert the curated artists. Artists that are already imported are not re-fetched from
    Spotify/iTunes (only their genres and display order are updated) unless `refresh` is set."""
    report = SyncReport()
    for order, (name, genres) in enumerate(curated):
        if only_genre and only_genre.lower() not in [g.lower() for g in genres]:
            continue

        existing_row = session.get(Artist, slugify(name))
        if existing_row is not None and not refresh and session.exec(
            select(Track.id).where(Track.artist_id == existing_row.id, Track.source == "spotify").limit(1)
        ).first():
            existing_row.genres = genres
            existing_row.sort_order = order
            session.add(existing_row)
            for track in session.exec(select(Track).where(Track.artist_id == existing_row.id, Track.source == "spotify")).all():
                track.genre = genres[0]
                session.add(track)
            session.commit()
            report.artists_unchanged_network += 1
            continue

        spotify_artist = spotify.find_artist(name)
        if not spotify_artist:
            log(f"  skip  {name}: no exact match on Spotify")
            report.artists_skipped.append(name)
            continue

        if spotify_artist.get("ambiguous"):
            log(f"  warn  {name}: several Spotify artists share this name, used the top hit")
            report.ambiguous.append(name)

        row = existing_row or session.exec(
            select(Artist).where(Artist.spotify_id == spotify_artist["id"])
        ).first()
        if row is None:
            images = spotify_artist.get("images") or []
            row = Artist(
                id=slugify(name),
                name=spotify_artist["name"],
                image_url=images[0]["url"] if images else _pick(IMAGE_URLS, name),
                bio=f"{spotify_artist['name']} · {', '.join(genres)}.",
                genres=genres,
                sort_order=order,
                followers="—",  # Spotify no longer exposes follower counts to dev-mode apps
                accent=_pick(ACCENTS, name),
                spotify_id=spotify_artist["id"],
            )
            report.artists_added += 1
        else:
            row.spotify_id = spotify_artist["id"]
            row.genres = genres
            row.sort_order = order
            report.artists_updated += 1
        session.add(row)
        session.flush()

        tracks = spotify.artist_tracks(spotify_artist, per_artist)
        songs = itunes.artist_songs(spotify_artist["name"]) if previews and tracks else []
        primary_genre = genres[0]
        for item in tracks:
            preview = match_preview(spotify_artist["name"], item["name"], songs) if previews else None
            existing = session.exec(select(Track).where(Track.spotify_id == item["id"])).first()
            if existing is None:
                existing = Track(
                    id=f"sp-{item['id']}",
                    title=item["name"],
                    artist_id=row.id,
                    genre=primary_genre,
                    release_year=release_year(item["album"]),
                    duration=format_duration(item["duration_ms"]),
                    color=_pick(ACCENTS, item["id"]),
                    spotify_id=item["id"],
                    spotify_uri=item["uri"],
                    source="spotify",
                )
                report.tracks_added += 1
            else:
                report.tracks_updated += 1
                if existing.artist_id == row.id:  # shared (collab) tracks stay with their first artist
                    existing.genre = primary_genre
            if preview:
                existing.preview_url = preview  # never overwrite a known preview with "no match"
            session.add(existing)
            if existing.preview_url:
                report.previews_matched += 1
            else:
                report.tracks_without_preview += 1
        session.commit()
        if previews and tracks and not any(t.preview_url for t in session.exec(select(Track).where(Track.artist_id == row.id, Track.source == "spotify")).all()):
            report.no_previews.append(name)
        log(f"  ok    {name}: {len(tracks)} tracks")
    return report
