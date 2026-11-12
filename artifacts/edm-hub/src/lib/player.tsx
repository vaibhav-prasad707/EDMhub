import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  getGetSpotifyStatusQueryKey,
  getSpotifyAccessToken,
  getSpotifyAuthorizeUrl,
  useDisconnectSpotify,
  useGetSpotifyStatus,
  type Track,
} from '@workspace/api-client-react';
import { loadSpotifySdk, type SpotifyPlayer, type SpotifyPlayerState } from '@/lib/spotify-sdk';

type SpotifyConnection = {
  connected: boolean; // the user has linked a Spotify account
  ready: boolean; // the in-browser Spotify device is up
  busy: boolean;
  connect: () => void;
  disconnect: () => void;
};

type PlayerState = {
  current: Track | null;
  playing: boolean;
  loading: boolean;
  error: string | null;
  currentTime: number;
  duration: number;
  volume: number;
  spotify: SpotifyConnection;
  canPlay: (track: Track) => boolean;
  playTrack: (track: Track, queue?: Track[]) => void;
  toggle: () => void;
  seek: (fraction: number) => void;
  setVolume: (volume: number) => void;
  next: () => void;
};

const PlayerContext = createContext<PlayerState | null>(null);

export function usePlayer(): PlayerState {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used inside PlayerProvider');
  return ctx;
}

// Spotify access tokens last an hour; keep one and refresh a minute early.
let cachedToken: { value: string; expiresAt: number } | null = null;
async function spotifyToken(): Promise<string> {
  if (cachedToken && cachedToken.expiresAt - Date.now() > 60_000) return cachedToken.value;
  const t = await getSpotifyAccessToken();
  cachedToken = { value: t.accessToken, expiresAt: Date.now() + t.expiresIn * 1000 };
  return t.accessToken;
}

export function PlayerProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const spotifyRef = useRef<SpotifyPlayer | null>(null);
  const deviceRef = useRef<string | null>(null);
  const engineRef = useRef<'preview' | 'spotify'>('preview');
  const queueRef = useRef<Track[]>([]);
  const currentRef = useRef<Track | null>(null);
  const volumeRef = useRef(0.8);
  const spotifyClock = useRef({ position: 0, at: 0, paused: true });
  const endedHandled = useRef(false);

  const [current, setCurrent] = useState<Track | null>(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolumeState] = useState(0.8);
  const [sdkReady, setSdkReady] = useState(false);
  const [connecting, setConnecting] = useState(false);

  const status = useGetSpotifyStatus({ query: { queryKey: getGetSpotifyStatusQueryKey(), staleTime: 60_000 } });
  const connected = status.data?.connected ?? false;
  const disconnectMutation = useDisconnectSpotify();

  const canPlay = useCallback(
    (track: Track) => Boolean(track.previewUrl) || Boolean(track.spotifyUri && sdkReady),
    [sdkReady],
  );

  const stopPreview = useCallback(() => {
    const audio = audioRef.current;
    if (audio && !audio.paused) audio.pause();
  }, []);

  const startPreview = useCallback((track: Track): boolean => {
    const audio = audioRef.current;
    if (!audio || !track.previewUrl) return false;
    engineRef.current = 'preview';
    currentRef.current = track;
    setCurrent(track);
    setCurrentTime(0);
    setDuration(0);
    setLoading(true);
    audio.src = track.previewUrl;
    audio.play().catch(err => {
      if (err?.name === 'AbortError') return; // superseded by a newer track
      setLoading(false);
      setPlaying(false);
      setError('Could not play this track');
    });
    return true;
  }, []);

  const startSpotify = useCallback(async (track: Track): Promise<boolean> => {
    const player = spotifyRef.current;
    const device = deviceRef.current;
    if (!player || !device || !track.spotifyUri) return false;
    stopPreview();
    engineRef.current = 'spotify';
    currentRef.current = track;
    endedHandled.current = false;
    setCurrent(track);
    setCurrentTime(0);
    setDuration(0);
    setLoading(true);
    try {
      const token = await spotifyToken();
      const res = await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${encodeURIComponent(device)}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ uris: [track.spotifyUri] }),
      });
      if (!res.ok) throw new Error(`Spotify returned ${res.status}`);
      return true;
    } catch {
      setLoading(false);
      return false;
    }
  }, [stopPreview]);

  const start = useCallback(async (track: Track) => {
    setError(null);
    if (track.spotifyUri && sdkReady) {
      if (await startSpotify(track)) return;
      // Spotify refused (account not allowlisted, no Premium, ...): fall back to the preview clip.
      if (startPreview(track)) { setError('Spotify playback unavailable, playing a preview'); return; }
      setError('Spotify playback failed for this account');
      return;
    }
    if (!startPreview(track)) setError('No audio available for this track');
  }, [sdkReady, startPreview, startSpotify]);

  const next = useCallback(() => {
    const queue = queueRef.current;
    const idx = queue.findIndex(t => t.id === currentRef.current?.id);
    if (idx >= 0 && queue.length > 1) void start(queue[(idx + 1) % queue.length]);
  }, [start]);

  // Preview engine: a plain <audio> element.
  useEffect(() => {
    const audio = new Audio();
    audio.preload = 'none';
    audio.volume = volumeRef.current;
    audioRef.current = audio;
    const isActive = () => engineRef.current === 'preview';
    const on = {
      play: () => isActive() && setPlaying(true),
      pause: () => isActive() && setPlaying(false),
      playing: () => isActive() && setLoading(false),
      waiting: () => isActive() && setLoading(true),
      timeupdate: () => isActive() && setCurrentTime(audio.currentTime),
      loadedmetadata: () => isActive() && setDuration(Number.isFinite(audio.duration) ? audio.duration : 0),
      ended: () => { if (!isActive()) return; setPlaying(false); next(); },
      error: () => {
        if (!isActive() || !audio.getAttribute('src')) return;
        setLoading(false);
        setPlaying(false);
        setError('Audio failed to load');
      },
    };
    Object.entries(on).forEach(([event, fn]) => audio.addEventListener(event, fn));
    return () => {
      Object.entries(on).forEach(([event, fn]) => audio.removeEventListener(event, fn));
      audio.pause();
      audio.removeAttribute('src');
    };
  }, [next]);

  // Spotify engine: the Web Playback SDK, only for users who linked an account.
  useEffect(() => {
    if (!connected) return;
    let cancelled = false;
    let player: SpotifyPlayer | null = null;
    loadSpotifySdk().then(() => {
      if (cancelled || !window.Spotify) return;
      player = new window.Spotify.Player({
        name: 'EDM Hub',
        volume: volumeRef.current,
        getOAuthToken: cb => { spotifyToken().then(cb).catch(() => setError('Spotify session expired, reconnect')); },
      });
      player.addListener('ready', ({ device_id }: { device_id: string }) => { deviceRef.current = device_id; setSdkReady(true); });
      player.addListener('not_ready', () => { deviceRef.current = null; setSdkReady(false); });
      const fail = (msg: string) => () => { setSdkReady(false); setError(msg); };
      player.addListener('initialization_error', fail('This browser cannot play Spotify tracks'));
      player.addListener('authentication_error', fail('Spotify login failed, reconnect'));
      player.addListener('account_error', fail('Spotify Premium is required for full tracks'));
      player.addListener('player_state_changed', (state: SpotifyPlayerState | null) => {
        if (!state || engineRef.current !== 'spotify') return;
        spotifyClock.current = { position: state.position, at: Date.now(), paused: state.paused };
        setCurrentTime(state.position / 1000);
        setDuration(state.duration / 1000);
        setPlaying(!state.paused);
        setLoading(false);
        // The SDK has no "ended" event: a finished track shows up as paused at 0 with itself in history.
        const uri = currentRef.current?.spotifyUri;
        if (state.paused && state.position === 0 && uri && state.track_window.previous_tracks.some(t => t.uri === uri) && !endedHandled.current) {
          endedHandled.current = true;
          next();
        }
      });
      spotifyRef.current = player;
      void player.connect();
    }).catch(() => setError('Could not load the Spotify player'));
    return () => {
      cancelled = true;
      player?.disconnect();
      spotifyRef.current = null;
      deviceRef.current = null;
      setSdkReady(false);
    };
  }, [connected, next]);

  // The SDK only reports state on changes, so advance the progress bar locally while playing.
  useEffect(() => {
    if (!playing || engineRef.current !== 'spotify') return;
    const id = window.setInterval(() => {
      const c = spotifyClock.current;
      if (!c.paused) setCurrentTime((c.position + (Date.now() - c.at)) / 1000);
    }, 500);
    return () => window.clearInterval(id);
  }, [playing]);

  const playTrack = useCallback((track: Track, queue?: Track[]) => {
    if (queue) queueRef.current = queue.filter(canPlay);
    else if (!queueRef.current.some(t => t.id === track.id)) queueRef.current = [track];
    // Clicking the track that is already loaded toggles it instead of restarting.
    if (currentRef.current?.id === track.id && (engineRef.current === 'spotify' || audioRef.current?.src)) {
      if (engineRef.current === 'spotify') void spotifyRef.current?.togglePlay();
      else {
        const audio = audioRef.current!;
        if (audio.paused) audio.play().catch(() => setError('Could not play this track'));
        else audio.pause();
      }
      return;
    }
    void spotifyRef.current?.activateElement(); // must run inside the click that starts playback
    void start(track);
  }, [canPlay, start]);

  const toggle = useCallback(() => {
    if (!currentRef.current) return;
    if (engineRef.current === 'spotify') { void spotifyRef.current?.togglePlay(); return; }
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) audio.play().catch(() => setError('Could not play this track'));
    else audio.pause();
  }, []);

  const seek = useCallback((fraction: number) => {
    const f = Math.min(Math.max(fraction, 0), 1);
    if (engineRef.current === 'spotify') {
      if (duration > 0) void spotifyRef.current?.seek(Math.round(f * duration * 1000));
      return;
    }
    const audio = audioRef.current;
    if (audio && Number.isFinite(audio.duration)) audio.currentTime = f * audio.duration;
  }, [duration]);

  const setVolume = useCallback((value: number) => {
    const v = Math.min(Math.max(value, 0), 1);
    volumeRef.current = v;
    if (audioRef.current) audioRef.current.volume = v;
    void spotifyRef.current?.setVolume(v);
    setVolumeState(v);
  }, []);

  const spotify = useMemo<SpotifyConnection>(() => ({
    connected,
    ready: sdkReady,
    busy: connecting || disconnectMutation.isPending,
    connect: () => {
      setConnecting(true);
      getSpotifyAuthorizeUrl()
        .then(r => window.location.assign(r.url))
        .catch(() => { setConnecting(false); setError('Spotify is not available right now'); });
    },
    disconnect: () => {
      disconnectMutation.mutate(undefined, {
        onSuccess: () => {
          cachedToken = null;
          if (engineRef.current === 'spotify') { currentRef.current = null; setCurrent(null); setPlaying(false); }
          qc.invalidateQueries({ queryKey: getGetSpotifyStatusQueryKey() });
        },
      });
    },
  }), [connected, sdkReady, connecting, disconnectMutation, qc]);

  const value = useMemo(
    () => ({ current, playing, loading, error, currentTime, duration, volume, spotify, canPlay, playTrack, toggle, seek, setVolume, next }),
    [current, playing, loading, error, currentTime, duration, volume, spotify, canPlay, playTrack, toggle, seek, setVolume, next],
  );
  return <PlayerContext.Provider value={value}>{children}</PlayerContext.Provider>;
}
