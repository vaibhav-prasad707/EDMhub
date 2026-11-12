import logging
import time
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://itunes.apple.com/search"
# Apple documents roughly 20 requests/minute; stay under it.
MIN_INTERVAL_SECONDS = 3.2


class ItunesClient:
    """Looks up 30-second preview clips on the public iTunes Search API (no key required)."""

    def __init__(self, min_interval: float = MIN_INTERVAL_SECONDS):
        self._min_interval = min_interval
        self._last_call = 0.0

    def artist_songs(self, artist_name: str) -> List[Dict[str, Any]]:
        """Songs credited to the artist that have a previewUrl (one request per artist)."""
        params = {"term": artist_name, "media": "music", "entity": "song", "attribute": "artistTerm", "limit": 200}
        for attempt in range(4):
            wait = self._min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            try:
                resp = requests.get(SEARCH_URL, params=params, timeout=20, headers={"User-Agent": "edm-hub-sync"})
            except requests.RequestException as exc:
                logger.warning("iTunes request failed (%s); retrying", exc)
                time.sleep(2 ** attempt)
                continue
            if resp.status_code in (403, 429):
                time.sleep(15 * (attempt + 1))  # rate limited: back off
                continue
            resp.raise_for_status()
            return [r for r in resp.json().get("results", []) if r.get("previewUrl")]
        logger.warning("Giving up on iTunes lookup for %s", artist_name)
        return []


itunes_client = ItunesClient()
