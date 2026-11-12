import logging
from typing import Any, Dict, List, Optional

import spotipy
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import settings
from app.lib.text import fold

logger = logging.getLogger(__name__)

# Dev-mode Spotify apps cap /search at 10 results per request.
SEARCH_PAGE = 10
# Variants we don't want as separate quiz entries.
_VARIANT_WORDS = ("remix", "live", "edit", "version", "mix", "instrumental", "acoustic", "demo", "sped up", "slowed", "remaster")


class SpotifyClient:
    """Server-side Spotify Web API client (Client Credentials flow: catalog metadata only)."""

    def __init__(self):
        if not settings.SPOTIPY_CLIENT_ID or not settings.SPOTIPY_CLIENT_SECRET:
            logger.warning("Spotify credentials not found. Spotify integration will be disabled.")
            self.sp = None
            return
        try:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=settings.SPOTIPY_CLIENT_ID,
                    client_secret=settings.SPOTIPY_CLIENT_SECRET,
                    cache_handler=MemoryCacheHandler(),  # never write a token file to disk
                ),
                retries=3,
                status_retries=3,
            )
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to initialize Spotify Client: {e}")
            self.sp = None

    def is_available(self) -> bool:
        return self.sp is not None

    def find_artist(self, name: str) -> Optional[Dict[str, Any]]:
        """Best exact-name match for an artist, or None. (No popularity/genres in dev mode.)"""
        if not self.is_available():
            return None
        result = self.sp.search(q=f'artist:"{name}"', type="artist", limit=SEARCH_PAGE)
        wanted = fold(name)
        for item in result["artists"]["items"]:
            if fold(item["name"]) == wanted:
                return item
        return None

    def artist_tracks(self, artist: Dict[str, Any], want: int = 6) -> List[Dict[str, Any]]:
        """Distinct, non-variant tracks credited to the artist (up to `want`)."""
        if not self.is_available():
            return []
        found: List[Dict[str, Any]] = []
        seen_titles = set()
        for offset in (0, SEARCH_PAGE):
            page = self.sp.search(q=f'artist:"{artist["name"]}"', type="track", limit=SEARCH_PAGE, offset=offset)
            for item in page["tracks"]["items"]:
                if artist["id"] not in {a["id"] for a in item["artists"]}:
                    continue
                title = item["name"]
                key = fold(title)
                if key in seen_titles or any(w in title.lower() for w in _VARIANT_WORDS):
                    continue
                seen_titles.add(key)
                found.append(item)
            if len(found) >= want:
                break
        return found[:want]


# Singleton instance for use throughout the app
spotify_client = SpotifyClient()
