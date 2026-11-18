"""Import the curated artists and their tracks from Spotify.

    cd artifacts/api-server-python
    python -m app.scripts.sync_spotify                 # everything
    python -m app.scripts.sync_spotify --genre Techno  # one genre
    python -m app.scripts.sync_spotify --no-previews   # skip the iTunes preview lookup
    python -m app.scripts.sync_spotify --refresh       # re-fetch artists that are already imported

By default artists that were imported before are not re-fetched (only their genres and display
order are refreshed), so re-running after editing the list only downloads the new artists.

Safe to re-run: rows are matched by Spotify ID, so nothing is duplicated.
"""
import argparse
import sys

from sqlmodel import Session, SQLModel

from app.db.migrate import apply_migrations
from app.db.session import engine
from app.lib.curated_artists import CURATED_ARTISTS
from app.lib.itunes_client import itunes_client
from app.lib.spotify_client import spotify_client
from app.lib.spotify_import import sync_catalog


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-artist", type=int, default=6, help="tracks to import per artist (default 6)")
    parser.add_argument("--genre", help="only artists tagged with this genre")
    parser.add_argument("--no-previews", action="store_true", help="skip iTunes preview matching")
    parser.add_argument("--refresh", action="store_true", help="re-fetch tracks for artists already imported")
    args = parser.parse_args(argv)

    if not spotify_client.is_available():
        print("SPOTIPY_CLIENT_ID / SPOTIPY_CLIENT_SECRET are not set (see .env.example).", file=sys.stderr)
        return 1

    SQLModel.metadata.create_all(engine)
    apply_migrations(engine)
    with Session(engine) as session:
        report = sync_catalog(
            session, spotify_client, itunes_client, CURATED_ARTISTS,
            per_artist=args.per_artist, only_genre=args.genre,
            previews=not args.no_previews, refresh=args.refresh, log=lambda m: print(m, flush=True),
        )
    print(report.summary())
    if report.artists_skipped:
        print("Not found on Spotify:", ", ".join(report.artists_skipped))
    if report.ambiguous:
        print("Name shared by several Spotify artists (check these):", ", ".join(report.ambiguous))
    if report.no_previews:
        print("Imported but no iTunes preview matched (not playable in the game):", ", ".join(report.no_previews))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
