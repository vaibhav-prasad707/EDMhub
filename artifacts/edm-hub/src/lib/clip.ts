import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Plays a short, capped audio clip on its own audio element. Deliberately separate from the
 * global player so the footer never shows (and gives away) which track is playing.
 */
export function useClip(maxSeconds = 12) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);

  const stop = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
    setPlaying(false);
  }, []);

  const play = useCallback((url: string) => {
    let audio = audioRef.current;
    if (!audio) {
      audio = new Audio();
      audio.preload = 'none';
      audio.addEventListener('timeupdate', () => {
        if (audio && audio.currentTime >= maxSeconds) {
          audio.pause();
          audio.currentTime = 0;
          setPlaying(false);
        }
      });
      audio.addEventListener('ended', () => setPlaying(false));
      audio.addEventListener('pause', () => setPlaying(false));
      audio.addEventListener('playing', () => setPlaying(true));
      audioRef.current = audio;
    }
    if (!audio.src.endsWith(url)) audio.src = url;
    audio.currentTime = 0;
    audio.play().catch(() => setPlaying(false));
  }, [maxSeconds]);

  useEffect(() => () => {
    audioRef.current?.pause();
    audioRef.current = null;
  }, []);

  return { playing, play, stop };
}
