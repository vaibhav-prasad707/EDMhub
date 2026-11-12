// Minimal typings for the parts of the Spotify Web Playback SDK this app uses.
export type SpotifyTrackRef = { uri: string };
export type SpotifyPlayerState = {
  paused: boolean;
  position: number; // ms
  duration: number; // ms
  track_window: { current_track: SpotifyTrackRef; previous_tracks: SpotifyTrackRef[] };
};

export interface SpotifyPlayer {
  connect(): Promise<boolean>;
  disconnect(): void;
  activateElement(): Promise<void>;
  togglePlay(): Promise<void>;
  pause(): Promise<void>;
  seek(positionMs: number): Promise<void>;
  setVolume(volume: number): Promise<void>;
  addListener(event: string, cb: (payload: any) => void): boolean;
}

declare global {
  interface Window {
    Spotify?: { Player: new (options: { name: string; getOAuthToken: (cb: (token: string) => void) => void; volume?: number }) => SpotifyPlayer };
    onSpotifyWebPlaybackSDKReady?: () => void;
  }
}

let sdkPromise: Promise<void> | null = null;

/** Loads Spotify's player script once. Resolves when window.Spotify is ready. */
export function loadSpotifySdk(): Promise<void> {
  if (window.Spotify) return Promise.resolve();
  if (!sdkPromise) {
    sdkPromise = new Promise<void>((resolve, reject) => {
      window.onSpotifyWebPlaybackSDKReady = () => resolve();
      const script = document.createElement('script');
      script.src = 'https://sdk.scdn.co/spotify-player.js';
      script.async = true;
      script.onerror = () => { sdkPromise = null; reject(new Error('Could not load the Spotify player')); };
      document.body.appendChild(script);
    });
  }
  return sdkPromise;
}
