import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { Track } from '@workspace/api-client-react';

type PlayerState = {
  current: Track | null;
  playing: boolean;
  loading: boolean;
  error: string | null;
  currentTime: number;
  duration: number;
  volume: number;
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

export function PlayerProvider({ children }: { children: ReactNode }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const queueRef = useRef<Track[]>([]);
  const currentRef = useRef<Track | null>(null);
  const [current, setCurrent] = useState<Track | null>(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolumeState] = useState(0.8);

  const start = useCallback((track: Track) => {
    const audio = audioRef.current;
    if (!audio) return;
    if (!track.previewUrl) {
      setError('No audio available for this track');
      return;
    }
    currentRef.current = track;
    setCurrent(track);
    setError(null);
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
  }, []);

  const next = useCallback(() => {
    const queue = queueRef.current;
    const idx = queue.findIndex(t => t.id === currentRef.current?.id);
    if (idx >= 0 && queue.length > 1) start(queue[(idx + 1) % queue.length]);
  }, [start]);

  useEffect(() => {
    const audio = new Audio();
    audio.preload = 'none';
    audio.volume = 0.8;
    audioRef.current = audio;
    const on = {
      play: () => setPlaying(true),
      pause: () => setPlaying(false),
      playing: () => setLoading(false),
      waiting: () => setLoading(true),
      timeupdate: () => setCurrentTime(audio.currentTime),
      loadedmetadata: () => setDuration(Number.isFinite(audio.duration) ? audio.duration : 0),
      ended: () => {
        setPlaying(false);
        next();
      },
      error: () => {
        if (!audio.getAttribute('src')) return;
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

  const playTrack = useCallback((track: Track, queue?: Track[]) => {
    const audio = audioRef.current;
    if (queue) queueRef.current = queue.filter(t => t.previewUrl);
    else if (!queueRef.current.some(t => t.id === track.id)) queueRef.current = [track];
    // Clicking the track that is already loaded toggles it instead of restarting.
    if (audio && currentRef.current?.id === track.id && audio.src) {
      if (audio.paused) audio.play().catch(() => setError('Could not play this track'));
      else audio.pause();
      return;
    }
    start(track);
  }, [start]);

  const toggle = useCallback(() => {
    const audio = audioRef.current;
    if (!audio || !currentRef.current) return;
    if (audio.paused) audio.play().catch(() => setError('Could not play this track'));
    else audio.pause();
  }, []);

  const seek = useCallback((fraction: number) => {
    const audio = audioRef.current;
    if (!audio || !Number.isFinite(audio.duration)) return;
    audio.currentTime = Math.min(Math.max(fraction, 0), 1) * audio.duration;
  }, []);

  const setVolume = useCallback((value: number) => {
    const v = Math.min(Math.max(value, 0), 1);
    if (audioRef.current) audioRef.current.volume = v;
    setVolumeState(v);
  }, []);

  const value = useMemo(
    () => ({ current, playing, loading, error, currentTime, duration, volume, playTrack, toggle, seek, setVolume, next }),
    [current, playing, loading, error, currentTime, duration, volume, playTrack, toggle, seek, setVolume, next],
  );
  return <PlayerContext.Provider value={value}>{children}</PlayerContext.Provider>;
}
