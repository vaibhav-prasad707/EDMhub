"""Import the curated artists and their tracks from Spotify.

    cd artifacts/api-server-python
    python -m app.scripts.sync_spotify                 # everything
    python -m app.scripts.sync_spotify --genre Techno  # one genre
    python -m app.scripts.sync_spotify --no-previews   # skip the iTunes preview lookup

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
            previews=not args.no_previews, log=print,
        )
    print(report.summary())
    if report.artists_skipped:
        print("Not found on Spotify:", ", ".join(report.artists_skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
