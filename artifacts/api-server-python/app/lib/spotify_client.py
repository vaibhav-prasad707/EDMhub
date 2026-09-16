import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SpotifyClient:
    def __init__(self):
        if not settings.SPOTIPY_CLIENT_ID or not settings.SPOTIPY_CLIENT_SECRET:
            logger.warning("Spotify credentials not found in environment variables. Spotify integration will be disabled.")
            self.sp = None
        else:
            try:
                auth_manager = SpotifyClientCredentials(
                    client_id=settings.SPOTIPY_CLIENT_ID,
                    client_secret=settings.SPOTIPY_CLIENT_SECRET
                )
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
                logger.info("Successfully initialized Spotify Client.")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify Client: {e}")
                self.sp = None

    def is_available(self) -> bool:
        return self.sp is not None

    def search_tracks_by_genre(self, genre: str, limit: int = 20):
        """
        Search for tracks in a specific genre.
        Returns a list of tracks from the Spotify API.
        """
        if not self.is_available():
            return []

        # Using the query format 'genre:genre_name'
        query = f'genre:{genre}'
        try:
            results = self.sp.search(q=query, type='track', limit=limit)
            return results['tracks']['items']
        except Exception as e:
            logger.error(f"Error searching Spotify for genre {genre}: {e}")
            return []

    def get_artist_details(self, artist_id: str):
        """
        Fetch detailed information for a specific artist.
        """
        if not self.is_available():
            return None

        try:
            return self.sp.artist(artist_id)
        except Exception as e:
            logger.error(f"Error fetching artist {artist_id}: {e}")
            return None

# Singleton instance for use throughout the app
spotify_client = SpotifyClient()
