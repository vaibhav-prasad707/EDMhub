import { type ReactNode, useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import {
  getGetArtistQueryKey,
  getGetDashboardQueryKey,
  getGetGameSessionQueryKey,
  getGetLeaderboardQueryKey,
  getGetRecommendationsQueryKey,
  getListArtistsQueryKey,
  getListActivityQueryKey,
  getListGenresQueryKey,
  GameStartInputDifficulty,
  GameStartInputRounds,
  useAnswerGameQuestion,
  useGetArtist,
  useGetDashboard,
  useGetGameSession,
  useGetLeaderboard,
  useGetRecommendations,
  useHealthCheck,
  useListActivity,
  useListArtists,
  useListGenres,
  useStartGame,
  useToggleArtistFavorite,
  type Artist,
  type GameQuestion,
  type GameSession,
  type LeaderboardEntry,
} from '@workspace/api-client-react';
import {
  Activity,
  ArrowUpRight,
  BarChart3,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Disc3,
  Headphones,
  Heart,
  Library as LibraryIcon,
  ListMusic,
  Menu,
  Music2,
  Play,
  Search,
  Sparkles,
  Trophy,
  UserRound,
  X,
  Zap,
} from 'lucide-react';
import { Link, Route, Switch, useLocation } from 'wouter';
import NotFound from '@/pages/not-found';

const queryClient = new QueryClient();
const colors = ['#c7ff23', '#ff3b9d', '#16d9d2', '#ff793f', '#a78bfa'];

function LoadingBlock({ label = 'Tuning the signal...' }: { label?: string }) {
  return <div className="ink-border bg-card p-6" data-testid="status-loading"><div className="h-3 w-28 animate-pulse bg-muted" /><div className="mt-4 h-8 w-3/4 animate-pulse bg-muted" /><p className="zine-label mt-5 text-muted-foreground">{label}</p></div>;
}

function QueryError({ onRetry }: { onRetry: () => void }) {
  return <div className="ink-border bg-[#ff793f] p-6 text-foreground" data-testid="status-error"><p className="zine-label">Signal lost / 404</p><h3 className="display mt-3 text-3xl">The booth went quiet.</h3><p className="mt-3 text-sm">We couldn’t load this crate. Try the connection again.</p><button onClick={onRetry} className="ink-border mt-5 bg-background px-4 py-2 text-sm font-bold hover:bg-primary" data-testid="button-retry">RECONNECT</button></div>;
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="ink-border bg-[#f3e8cf] p-8 text-center" data-testid="status-empty"><Disc3 className="mx-auto mb-4 h-9 w-9" /><p className="zine-label">Nothing in the pile yet</p><h3 className="display mt-3 text-3xl">{title}</h3><p className="mx-auto mt-3 max-w-md text-sm text-muted-foreground">{detail}</p></div>;
}

function Shell({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const nav = [
    { href: '/', label: 'Overview', icon: BarChart3 },
    { href: '/discover', label: 'Discover', icon: Search },
    { href: '/game', label: 'Guess the Track', icon: CircleHelp },
    { href: '/leaderboard', label: 'Leaderboard', icon: Trophy },
    { href: '/library', label: 'My Library', icon: LibraryIcon },
    { href: '/profile', label: 'Profile', icon: UserRound },
  ];
  return <div className="paper-grain min-h-[100dvh] bg-background pb-24">
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-[252px] flex-col bg-sidebar px-5 py-6 text-sidebar-foreground transition-transform md:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="mb-12 flex items-center justify-between"><Link href="/" className="flex items-center gap-3" data-testid="link-logo"><span className="grid h-10 w-10 place-items-center border-2 border-primary bg-primary text-xl font-black text-sidebar"><Music2 /></span><span className="display text-2xl tracking-[-.08em]">EDM<br />HUB<span className="text-primary">.</span></span></Link><button className="md:hidden" onClick={() => setMobileOpen(false)} data-testid="button-close-menu"><X /></button></div>
      <div className="zine-label mb-3 text-primary">Your frequency</div>
      <nav className="space-y-1" aria-label="Main navigation">{nav.map(({ href, label, icon: Icon }) => <Link key={href} href={href} onClick={() => setMobileOpen(false)} className={`flex items-center gap-3 border-2 border-transparent px-3 py-3 text-sm font-bold transition hover:border-primary hover:bg-primary/10 ${location === href ? 'border-primary bg-primary text-sidebar' : ''}`} data-testid={`link-nav-${label.toLowerCase().replaceAll(' ', '-')}`}><Icon size={18} strokeWidth={2.3} /><span>{label}</span>{location === href && <ChevronRight className="ml-auto" size={16} />}</Link>)}</nav>
      <div className="mt-auto border-t border-sidebar-foreground/30 pt-5"><div className="zine-label text-sidebar-foreground/60">Session status</div><div className="mt-3 flex items-center gap-2 text-sm"><span className="h-2 w-2 rounded-full bg-primary" /> Live crate active</div><div className="mt-5 flex gap-2"><span className="border border-sidebar-foreground/40 px-2 py-1 text-[10px]">V. 02</span><span className="border border-sidebar-foreground/40 px-2 py-1 text-[10px]">SF / 2024</span></div></div>
    </aside>
    {mobileOpen && <button className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={() => setMobileOpen(false)} aria-label="Close navigation" data-testid="button-overlay-close" />}
    <main className="md:pl-[252px]"><header className="sticky top-0 z-20 flex h-[72px] items-center justify-between border-b-2 border-foreground bg-background/95 px-5 backdrop-blur md:px-9"><button className="md:hidden" onClick={() => setMobileOpen(true)} data-testid="button-open-menu"><Menu /></button><div className="hidden items-center gap-2 md:flex"><span className="zine-label">EDM HUB /</span><span className="text-sm font-bold capitalize">{location === '/' ? 'overview' : location.slice(1)}</span></div><div className="ml-auto flex items-center gap-3"><div className="hidden items-center gap-2 border-2 border-foreground bg-card px-3 py-2 sm:flex"><span className="h-2 w-2 rounded-full bg-[#ff3b9d]" /><span className="zine-label">Broadcasting now</span></div><Link href="/profile" className="grid h-9 w-9 place-items-center border-2 border-foreground bg-primary font-bold" data-testid="link-header-profile">AJ</Link></div></header>{children}</main>
    <Player />
  </div>;
}

function Player() {
  const [playing, setPlaying] = useState(false);
  return <div className="fixed bottom-0 left-0 right-0 z-30 border-t-2 border-foreground bg-[#ff3b9d] px-4 py-3 md:left-[252px]"><div className="mx-auto flex max-w-[1400px] items-center gap-4"><button onClick={() => setPlaying(!playing)} className="grid h-10 w-10 shrink-0 place-items-center border-2 border-foreground bg-primary hover:bg-card" data-testid="button-player-toggle">{playing ? <span className="font-bold">Ⅱ</span> : <Play size={16} fill="currentColor" />}</button><div className="min-w-0 flex-1"><div className="flex items-center gap-2"><p className="truncate text-sm font-bold">Night Shift Radio</p>{playing && <span className="music-eq text-foreground"><i /><i /><i /><i /></span>}</div><p className="zine-label truncate opacity-70">EDM HUB SELECTS / SIGNAL 004</p></div><div className="hidden items-center gap-2 sm:flex"><span className="zine-label">01:24</span><div className="h-1 w-28 bg-foreground/30"><div className="h-full w-1/3 bg-foreground" /></div><span className="zine-label">03:48</span></div><button className="hidden border-l-2 border-foreground pl-4 sm:block" data-testid="button-player-queue"><ListMusic size={19} /></button></div></div>;
}

function PageFrame({ eyebrow, title, intro, children, accent = '#c7ff23' }: { eyebrow: string; title: string; intro?: string; children: ReactNode; accent?: string }) {
  return <div className="mx-auto max-w-[1400px] px-5 py-8 md:px-9 md:py-12"><div className="animate-rise mb-10 flex flex-col justify-between gap-5 border-b-2 border-foreground pb-8 md:flex-row md:items-end"><div><p className="zine-label mb-4 flex items-center gap-2"><span className="inline-block h-2 w-2" style={{ backgroundColor: accent }} />{eyebrow}</p><h1 className="display max-w-4xl text-6xl md:text-8xl">{title}</h1>{intro && <p className="mt-5 max-w-xl text-base text-muted-foreground">{intro}</p>}</div><div className="hidden rotate-[-4deg] border-2 border-foreground bg-[#ff793f] px-4 py-3 text-center md:block"><span className="zine-label block">Printed matter</span><span className="display text-xl">NO. 0024</span></div></div>{children}</div>;
}

function StatTile({ label, value, detail, color = '#c7ff23' }: { label: string; value: string | number; detail?: string; color?: string }) {
  return <div className="ink-border hover-lift bg-card p-5" style={{ borderTop: `9px solid ${color}` }} data-testid={`stat-${label.toLowerCase().replaceAll(' ', '-')}`}><p className="zine-label text-muted-foreground">{label}</p><div className="mt-3 flex items-end justify-between gap-2"><strong className="display text-4xl">{value}</strong>{detail && <span className="text-xs font-bold text-muted-foreground">{detail}</span>}</div></div>;
}

function ArtistCard({ artist, onFavorite, onOpen }: { artist: Artist; onFavorite: (artist: Artist) => void; onOpen: (artist: Artist) => void }) {
  return <article className="group ink-border hover-lift relative overflow-hidden bg-card" data-testid={`card-artist-${artist.id}`}><button onClick={() => onFavorite(artist)} className="absolute right-3 top-3 z-10 grid h-9 w-9 place-items-center border-2 border-foreground bg-background hover:bg-primary" aria-label={`${artist.isFavorite ? 'Remove' : 'Save'} ${artist.name}`} data-testid={`button-favorite-${artist.id}`}><Heart size={17} fill={artist.isFavorite ? 'currentColor' : 'none'} /></button><button onClick={() => onOpen(artist)} className="block w-full text-left" data-testid={`button-open-artist-${artist.id}`}><div className="relative h-56 overflow-hidden" style={{ backgroundColor: artist.accent || '#c7ff23' }}><img src={artist.imageUrl} alt={artist.name} className="h-full w-full object-cover mix-blend-multiply grayscale-[.2] transition duration-500 group-hover:scale-105 group-hover:mix-blend-normal" /><span className="absolute bottom-3 left-3 border-2 border-foreground bg-primary px-2 py-1 text-[10px] font-bold uppercase">{artist.genres?.[0] || 'Electronic'}</span></div><div className="p-4"><h3 className="display text-2xl">{artist.name}</h3><p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{artist.bio}</p><div className="mt-4 flex items-center justify-between border-t border-foreground/20 pt-3"><span className="zine-label">{artist.followers} followers</span><ChevronRight size={16} /></div></div></button></article>;
}

function ArtistDrawer({ artistId, onClose }: { artistId: string; onClose: () => void }) {
  const { data, isLoading, isError, refetch } = useGetArtist(artistId, { query: { queryKey: getGetArtistQueryKey(artistId) } });
  return <div className="fixed inset-0 z-50 flex justify-end bg-foreground/40" onClick={onClose}><section className="h-full w-full max-w-xl overflow-y-auto border-l-2 border-foreground bg-background p-6 md:p-9" onClick={e => e.stopPropagation()}><button onClick={onClose} className="mb-8 ml-auto grid h-10 w-10 place-items-center border-2 border-foreground bg-primary" data-testid="button-close-artist"><X /></button>{isLoading && <LoadingBlock label="Pulling the artist file..." />}{isError && <QueryError onRetry={() => refetch()} />}{data && <><p className="zine-label">Artist file / {data.genres?.join(' · ')}</p><h2 className="display mt-3 text-6xl">{data.name}</h2><img src={data.imageUrl} alt={data.name} className="mt-7 h-64 w-full object-cover ink-border" /><p className="mt-6 text-base leading-7">{data.bio}</p><div className="mt-8 flex items-center gap-3"><span className="border-2 border-foreground bg-[#16d9d2] px-3 py-2 font-bold">{data.followers}</span><span className="zine-label">listeners in the wild</span></div><h3 className="display mt-12 text-3xl">Top tracks</h3><div className="mt-4 divide-y-2 divide-foreground border-y-2 border-foreground">{data.topTracks?.map((track, i) => <div key={track.id} className="flex items-center gap-3 py-4"><span className="zine-label w-6">0{i + 1}</span><div className="h-10 w-10" style={{ background: track.color }} /><div className="min-w-0 flex-1"><p className="truncate font-bold">{track.title}</p><p className="zine-label text-muted-foreground">{track.genre} / {track.releaseYear}</p></div><span className="zine-label">{track.duration}</span></div>)}</div></>}</section></div>;
}

function Overview() {
  const { data, isLoading, isError, refetch } = useGetDashboard({ query: { queryKey: getGetDashboardQueryKey() } });
  const { data: activity } = useListActivity({ query: { queryKey: getListActivityQueryKey() } });
  const { data: health } = useHealthCheck();
  if (isLoading) return <PageFrame eyebrow="Your desk / loading" title="A new crate is arriving."><LoadingBlock /></PageFrame>;
  if (isError || !data) return <PageFrame eyebrow="Your desk / offline" title="The desk is waiting."><QueryError onRetry={() => refetch()} /></PageFrame>;
  return <PageFrame eyebrow={`Good afternoon, ${data.profile.username}`} title="Keep digging." intro="A quick read on your listening brain, your current obsessions, and the next track worth knowing."><div className="grid gap-5 lg:grid-cols-[1.5fr_1fr_1fr]"><div className="animate-rise delay-1 ink-border hard-shadow bg-[#ff3b9d] p-6 md:p-8"><div className="flex items-start justify-between"><div><p className="zine-label">Artist of the week</p><h2 className="display mt-6 max-w-lg text-5xl md:text-7xl">{data.stats.artistOfWeek}</h2></div><Sparkles /></div><div className="mt-10 flex items-end justify-between border-t-2 border-foreground pt-4"><span className="zine-label">The one your friends will ask about next</span><Link href="/discover" className="border-2 border-foreground bg-primary px-3 py-2 text-xs font-bold" data-testid="link-discover-week">READ FILE <ArrowUpRight className="inline" size={14} /></Link></div></div><StatTile label="Games played" value={data.stats.gamesPlayed} detail="all time" color="#16d9d2" /><StatTile label="Accuracy" value={`${data.stats.accuracy}%`} detail="last 30 days" color="#ff793f" /></div><div className="mt-7 grid gap-5 lg:grid-cols-[1.15fr_.85fr]"><section className="ink-border bg-card p-5 md:p-7"><div className="flex items-center justify-between"><div><p className="zine-label">Knowledge map</p><h2 className="display mt-2 text-3xl">Your genres in rotation</h2></div><span className="border-2 border-foreground bg-primary px-2 py-1 text-[10px] font-bold">LIVE DATA</span></div><div className="mt-7 space-y-5">{data.genreBreakdown?.map((genre, i) => <div key={genre.genre} data-testid={`row-genre-${i}`}><div className="mb-2 flex justify-between text-sm font-bold"><span>{genre.genre}</span><span>{genre.value}%</span></div><div className="h-4 border-2 border-foreground bg-muted"><div className="h-full" style={{ width: `${Math.min(100, genre.value)}%`, background: genre.color || colors[i % colors.length] }} /></div></div>)}</div></section><section className="ink-border bg-[#16d9d2] p-5 md:p-7"><div className="flex items-center justify-between"><div><p className="zine-label">Signal / {health?.status || 'online'}</p><h2 className="display mt-2 text-3xl">Recent activity</h2></div><Activity size={25} /></div><div className="mt-5 divide-y-2 divide-foreground">{activity?.slice(0, 4).map(item => <div className="py-3" key={item.id} data-testid={`activity-${item.id}`}><p className="text-sm font-bold">{item.title}</p><p className="mt-1 text-xs">{item.detail}</p></div>) || <p className="py-6 text-sm">Your next move will appear here.</p>}</div><Link href="/profile" className="mt-5 inline-flex items-center gap-2 border-2 border-foreground bg-background px-3 py-2 text-xs font-bold" data-testid="link-view-activity">VIEW ALL <ChevronRight size={14} /></Link></section></div><section className="mt-7"><div className="mb-4 flex items-end justify-between"><div><p className="zine-label">Saved frequency</p><h2 className="display mt-2 text-4xl">Your favorites</h2></div><Link href="/library" className="text-sm font-bold underline" data-testid="link-view-library">OPEN LIBRARY <ArrowUpRight className="inline" size={14} /></Link></div>{data.favoriteArtists?.length ? <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{data.favoriteArtists.slice(0, 4).map(artist => <ArtistCard key={artist.id} artist={artist} onFavorite={() => {}} onOpen={() => {}} />)}</div> : <EmptyState title="No repeat offenders." detail="Save an artist from Discover and they’ll land here, ready for another listen." />}</section></PageFrame>;
}

function Discover() {
  const [search, setSearch] = useState('');
  const [genre, setGenre] = useState('');
  const [drawer, setDrawer] = useState<string | null>(null);
  const genres = useListGenres({ query: { queryKey: getListGenresQueryKey() } });
  const params = useMemo(() => ({ search: search || undefined, genre: genre || undefined, limit: 24 }), [search, genre]);
  const artists = useListArtists(params, { query: { queryKey: getListArtistsQueryKey(params) } });
  const recs = useGetRecommendations({ genres: genre || undefined }, { query: { queryKey: getGetRecommendationsQueryKey({ genres: genre || undefined }) } });
  const favorite = useToggleArtistFavorite();
  const queryClient = useQueryClient();
  const onFavorite = (artist: Artist) => favorite.mutate({ artistId: artist.id }, { onSuccess: state => { queryClient.invalidateQueries({ queryKey: getListArtistsQueryKey(params) }); queryClient.invalidateQueries({ queryKey: getGetRecommendationsQueryKey({ genres: genre || undefined }) }); queryClient.invalidateQueries({ queryKey: getGetDashboardQueryKey() }); void state; } });
  return <PageFrame eyebrow="Field notes / discovery" title="Find your next obsession." intro="Browse the artists shaping the edges of electronic music. Search by name, pull a genre thread, and follow it until the floor disappears."><div className="mb-8 grid gap-3 md:grid-cols-[1fr_auto]"><label className="flex items-center gap-3 border-2 border-foreground bg-card px-4 py-3"><Search size={20} /><input value={search} onChange={e => setSearch(e.target.value)} className="w-full bg-transparent outline-none placeholder:text-muted-foreground" placeholder="Search artists, scenes, aliases..." data-testid="input-search-artists" /></label><label className="relative flex items-center border-2 border-foreground bg-[#c7ff23] px-4 py-3"><select value={genre} onChange={e => setGenre(e.target.value)} className="appearance-none bg-transparent pr-8 text-sm font-bold outline-none" data-testid="select-genre"><option value="">ALL GENRES</option>{genres.data?.map(g => <option value={g.name} key={g.id}>{g.name.toUpperCase()} / {g.count}</option>)}</select><ChevronDown className="pointer-events-none absolute right-3" size={16} /></label></div><div className="mb-10 flex gap-3 overflow-x-auto pb-2">{genres.data?.slice(0, 7).map((g, i) => <button onClick={() => setGenre(genre === g.name ? '' : g.name)} key={g.id} className={`shrink-0 border-2 border-foreground px-3 py-2 text-xs font-bold ${genre === g.name ? 'bg-[#ff3b9d]' : 'bg-card hover:bg-primary'}`} data-testid={`button-filter-${g.id}`}>{g.name}</button>)}</div>{search === '' && !genre && recs.data?.length ? <section className="mb-12"><div className="mb-4 flex items-end justify-between"><div><p className="zine-label">Curated for your ears</p><h2 className="display mt-2 text-4xl">The recommendation stack</h2></div><span className="zine-label">{recs.data.length} dispatches</span></div><div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{recs.data.slice(0, 4).map(a => <ArtistCard key={a.id} artist={a} onFavorite={onFavorite} onOpen={a => setDrawer(a.id)} />)}</div></section> : null}<section><div className="mb-4 flex items-end justify-between border-t-2 border-foreground pt-7"><div><p className="zine-label">{search || genre ? 'Filtered artists' : 'All signal'}</p><h2 className="display mt-2 text-4xl">{search || genre ? 'Your results.' : 'The wider scene.'}</h2></div><span className="zine-label">{artists.data?.length || 0} artists</span></div>{artists.isLoading ? <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4"><LoadingBlock /><LoadingBlock /><LoadingBlock /><LoadingBlock /></div> : artists.isError ? <QueryError onRetry={() => artists.refetch()} /> : artists.data?.length ? <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{artists.data.map(a => <ArtistCard key={a.id} artist={a} onFavorite={onFavorite} onOpen={a => setDrawer(a.id)} />)}</div> : <EmptyState title="No artists on this wavelength." detail="Try a broader search or peel back the genre filter." />}</section>{drawer && <ArtistDrawer artistId={drawer} onClose={() => setDrawer(null)} />}</PageFrame>;
}

function Game() {
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [rounds, setRounds] = useState<5 | 10 | 20>(10);
  const [genre, setGenre] = useState('');
  const [era, setEra] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [current, setCurrent] = useState<GameSession | null>(null);
  const [question, setQuestion] = useState<GameQuestion | null>(null);
  const [hint, setHint] = useState(false);
  const [answered, setAnswered] = useState<{ correct: boolean; correctId: string; points: number } | null>(null);
  const genres = useListGenres({ query: { queryKey: getListGenresQueryKey() } });
  const sessionQuery = useGetGameSession(sessionId, { query: { enabled: !!sessionId, queryKey: getGetGameSessionQueryKey(sessionId) } });
  const start = useStartGame();
  const answer = useAnswerGameQuestion();
  const begin = () => start.mutate({ data: { difficulty, rounds, genre: genre || null, era: era || null } }, { onSuccess: data => { setSessionId(data.id); setCurrent(data); setQuestion(data.question); setAnswered(null); setHint(false); } });
  const submit = (optionId: string) => { if (!sessionId || !question || answered || answer.isPending) return; answer.mutate({ sessionId, data: { questionId: question.id, optionId, responseTimeMs: 4200, hintsUsed: hint ? 1 : 0 } }, { onSuccess: result => { setAnswered({ correct: result.correct, correctId: result.correctOptionId, points: result.pointsEarned }); setCurrent(prev => prev ? { ...prev, score: result.totalScore, streak: result.streak, completed: result.completed } : prev); if (result.nextQuestion && !result.completed) { setTimeout(() => { setQuestion(result.nextQuestion as GameQuestion); setAnswered(null); setHint(false); }, 900); } } }); };
  if (current && question) return <PageFrame eyebrow={`Guess the track / ${current.difficulty} mode`} title={current.completed ? 'Set complete.' : `Round ${current.currentRound} of ${current.rounds}.`} intro={current.completed ? `You scored ${current.score} points with a ${current.streak} track streak. The crate remembers.` : 'Listen closely. Every detail is a clue, but only one answer belongs to this clip.'} accent="#ff3b9d"><div className="grid gap-6 lg:grid-cols-[1fr_380px]"><section className="ink-border hard-shadow bg-[#ff3b9d] p-6 md:p-10"><div className="flex items-center justify-between"><span className="zine-label">Clip / {question.clipLabel}</span><span className="border-2 border-foreground bg-primary px-2 py-1 text-xs font-bold">+{current.streak} STREAK</span></div><div className="my-16 text-center"><div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full border-2 border-foreground bg-primary"><Headphones size={38} /></div><p className="zine-label">Press play, trust the feeling</p><h2 className="display mt-4 text-5xl md:text-7xl">{answered ? (answered.correct ? 'That’s the one.' : 'Not this time.') : 'Who made this?'}</h2><button className="mt-7 inline-flex items-center gap-3 border-2 border-foreground bg-background px-6 py-3 font-bold" data-testid="button-play-clip"><Play size={18} fill="currentColor" /> PLAY 12 SEC CLIP</button></div>{!answered && <button onClick={() => setHint(true)} disabled={hint} className="flex items-center gap-2 border-t-2 border-foreground pt-4 text-xs font-bold disabled:opacity-50" data-testid="button-use-hint"><Zap size={15} /> {hint ? `HINT: ${question.genre} / ${question.releaseYear}` : 'USE A HINT (-25 PTS)'}</button>}{answered && <div className="border-t-2 border-foreground pt-4 text-sm font-bold">{answered.correct ? `Correct. +${answered.points} points.` : `The answer was ${question.options.find(o => o.id === answered.correctId)?.artistName || 'in the crate'}.`}</div>}</section><aside className="ink-border bg-card p-5 md:p-7"><div className="mb-5 flex justify-between"><p className="zine-label">Pick one</p><span className="zine-label">Score {current.score}</span></div><div className="space-y-3">{question.options.map((option, i) => <button key={option.id} onClick={() => submit(option.id)} disabled={!!answered || answer.isPending} className={`group flex w-full items-center gap-3 border-2 border-foreground p-4 text-left transition hover:-translate-x-1 hover:bg-primary disabled:cursor-default ${answered && option.id === answered.correctId ? 'bg-[#c7ff23]' : answered && option.id !== answered.correctId ? 'opacity-50' : 'bg-background'}`} data-testid={`button-answer-${option.id}`}><span className="grid h-7 w-7 place-items-center border-2 border-foreground text-xs font-bold">{String.fromCharCode(65 + i)}</span><span><strong className="block">{option.artistName}</strong><span className="text-xs text-muted-foreground">{option.title}</span></span></button>)}</div>{sessionQuery.isError && <p className="mt-4 text-xs text-[#d8471b]">Live sync is delayed, but your answer is queued.</p>}</aside></div></PageFrame>;
  return <PageFrame eyebrow="The listening game / daily edition" title="Name that track." intro="A twelve-second clip. Four plausible answers. One chance to prove you really listen."><div className="grid gap-6 lg:grid-cols-[1.2fr_.8fr]"><section className="ink-border hard-shadow bg-[#16d9d2] p-6 md:p-10"><div className="flex justify-between"><span className="zine-label">Session setup / 01</span><span className="display text-2xl">QUIZ</span></div><h2 className="display mt-12 max-w-xl text-6xl md:text-8xl">How deep is your crate?</h2><p className="mt-7 max-w-md">Choose the pressure, then let the first kick drum tell you everything.</p><button disabled={start.isPending} onClick={begin} className="mt-12 inline-flex items-center gap-3 border-2 border-foreground bg-primary px-6 py-4 font-bold hover:bg-background disabled:opacity-60" data-testid="button-start-game">{start.isPending ? 'LOADING THE ROOM...' : 'START SESSION'} <ArrowUpRight size={18} /></button></section><section className="ink-border bg-card p-6 md:p-8"><p className="zine-label">Tune the rules</p><div className="mt-7"><label className="zine-label block">Difficulty</label><div className="mt-3 grid grid-cols-3 gap-2">{(['easy', 'medium', 'hard'] as const).map(level => <button key={level} onClick={() => setDifficulty(level)} className={`border-2 border-foreground px-2 py-3 text-xs font-bold uppercase ${difficulty === level ? 'bg-[#ff3b9d]' : 'bg-background'}`} data-testid={`button-difficulty-${level}`}>{level}</button>)}</div></div><div className="mt-7"><label className="zine-label block">Rounds</label><div className="mt-3 grid grid-cols-3 gap-2">{([5, 10, 20] as const).map(num => <button key={num} onClick={() => setRounds(num)} className={`border-2 border-foreground px-2 py-3 text-xs font-bold ${rounds === num ? 'bg-primary' : 'bg-background'}`} data-testid={`button-rounds-${num}`}>{num} TRACKS</button>)}</div></div><div className="mt-7"><label className="zine-label block" htmlFor="game-genre">Genre filter</label><select id="game-genre" value={genre} onChange={e => setGenre(e.target.value)} className="mt-3 w-full border-2 border-foreground bg-background p-3 text-sm font-bold" data-testid="select-game-genre"><option value="">ANY GENRE</option>{genres.data?.map(g => <option value={g.name} key={g.id}>{g.name}</option>)}</select></div><div className="mt-7"><label className="zine-label block" htmlFor="game-era">Era filter</label><select id="game-era" value={era} onChange={e => setEra(e.target.value)} className="mt-3 w-full border-2 border-foreground bg-background p-3 text-sm font-bold" data-testid="select-game-era"><option value="">ANY ERA</option><option value="2000s">2000s</option><option value="2010s">2010s</option><option value="2020s">2020s</option></select></div></section></div></PageFrame>;
}

function Leaderboard() {
  const { data, isLoading, isError, refetch } = useGetLeaderboard({ query: { queryKey: getGetLeaderboardQueryKey() } });
  return <PageFrame eyebrow="The scoreboard / all time" title="Who knows the most?" intro="A running list of sharp ears, deep memories, and suspiciously good guesses. Your rank is waiting somewhere in the noise." accent="#ff793f"><div className="grid gap-6 lg:grid-cols-[.75fr_1.25fr]"><div className="ink-border hard-shadow bg-[#ff793f] p-7"><p className="zine-label">Your current position</p><div className="mt-5 flex items-baseline gap-3"><span className="display text-8xl">{data?.currentUserRank ? `#${data.currentUserRank}` : '—'}</span><span className="text-sm font-bold">/ {data?.totalPlayers || '—'} players</span></div><div className="mt-12 border-t-2 border-foreground pt-4 text-sm">Keep playing to climb. The leaderboard updates after each finished session.</div><Link href="/game" className="mt-7 inline-flex items-center gap-2 border-2 border-foreground bg-primary px-4 py-3 text-sm font-bold" data-testid="link-leaderboard-game">PLAY FOR POINTS <ArrowUpRight size={16} /></Link></div><section className="ink-border bg-card p-4 md:p-7">{isLoading && <LoadingBlock label="Counting the crowd..." />}{isError && <QueryError onRetry={() => refetch()} />}{data?.entries?.length ? <div className="overflow-x-auto"><div className="mb-4 grid min-w-[600px] grid-cols-[70px_1fr_120px_100px] border-b-2 border-foreground px-4 pb-3"><span className="zine-label">Rank</span><span className="zine-label">Player</span><span className="zine-label">Score</span><span className="zine-label">Accuracy</span></div><div className="min-w-[600px]">{data.entries.map((entry, index) => <LeaderboardRow key={entry.username + index} entry={entry} index={index} />)}</div></div> : !isLoading && <EmptyState title="The board is blank." detail="Play your first session and be the name everyone has to beat." />}</section></div></PageFrame>;
}

function LeaderboardRow({ entry, index }: { entry: LeaderboardEntry; index: number }) {
  return <div className={`grid grid-cols-[70px_1fr_120px_100px] items-center border-b border-foreground/20 px-4 py-4 ${entry.isCurrentUser ? 'bg-primary' : ''}`} data-testid={`row-leaderboard-${index}`}><span className="display text-3xl">{entry.rank < 4 ? ['01', '02', '03'][entry.rank - 1] : entry.rank}</span><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center border-2 border-foreground text-xs font-bold" style={{ background: entry.accent }}>{entry.initials}</span><div><strong className="block">{entry.username}{entry.isCurrentUser && <span className="ml-2 text-[10px]">YOU</span>}</strong><span className="zine-label text-muted-foreground">{entry.games} sessions</span></div></div><strong>{entry.score.toLocaleString()}</strong><span className="text-sm font-bold">{entry.accuracy}%</span></div>;
}

function Library() {
  const dash = useGetDashboard({ query: { queryKey: getGetDashboardQueryKey() } });
  const [drawer, setDrawer] = useState<string | null>(null);
  const favorite = useToggleArtistFavorite();
  const queryClient = useQueryClient();
  const onFavorite = (a: Artist) => favorite.mutate({ artistId: a.id }, { onSuccess: () => { queryClient.invalidateQueries({ queryKey: getGetDashboardQueryKey() }); } });
  return <PageFrame eyebrow="The private shelf / saved" title="Your library." intro="The artists and tracks you marked for later, organized like a good record store counter."><div className="mb-7 flex items-center gap-3"><span className="border-2 border-foreground bg-primary px-3 py-2 text-xs font-bold">ARTISTS {dash.data?.favoriteArtists?.length || 0}</span><span className="border-2 border-foreground bg-card px-3 py-2 text-xs font-bold">TRACKS / VIA ARTISTS</span></div>{dash.isLoading ? <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4"><LoadingBlock /><LoadingBlock /><LoadingBlock /><LoadingBlock /></div> : dash.isError ? <QueryError onRetry={() => dash.refetch()} /> : dash.data?.favoriteArtists?.length ? <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{dash.data.favoriteArtists.map(a => <ArtistCard key={a.id} artist={a} onFavorite={onFavorite} onOpen={a => setDrawer(a.id)} />)}</div> : <EmptyState title="Your shelf is empty." detail="Favorite an artist while you’re digging through Discover. We’ll keep the lights on." />}{drawer && <ArtistDrawer artistId={drawer} onClose={() => setDrawer(null)} />}</PageFrame>;
}

function Profile() {
  const { data: dash, isLoading, isError, refetch } = useGetDashboard({ query: { queryKey: getGetDashboardQueryKey() } });
  const { data: activity } = useListActivity({ query: { queryKey: getListActivityQueryKey() } });
  if (isLoading) return <PageFrame eyebrow="Player profile / loading" title="Reading your notes."><LoadingBlock /></PageFrame>;
  if (isError || !dash) return <PageFrame eyebrow="Player profile / offline" title="Profile unavailable."><QueryError onRetry={() => refetch()} /></PageFrame>;
  return <PageFrame eyebrow="Player profile / field notes" title={dash.profile.username} intro={dash.profile.bio} accent="#a78bfa"><div className="grid gap-6 lg:grid-cols-[.8fr_1.2fr]"><section className="ink-border hard-shadow bg-[#a78bfa] p-7"><div className="grid h-20 w-20 place-items-center border-2 border-foreground bg-primary text-3xl font-black">{dash.profile.initials}</div><p className="zine-label mt-8">Member since</p><p className="mt-2 font-bold">{dash.profile.memberSince}</p><div className="mt-10 border-t-2 border-foreground pt-4"><p className="zine-label">Favorite genre</p><p className="display mt-2 text-4xl">{dash.stats.favoriteGenre}</p></div></section><section className="grid gap-4 sm:grid-cols-2"><StatTile label="Total points" value={dash.stats.totalPoints.toLocaleString()} color="#c7ff23" /><StatTile label="Best streak" value={dash.stats.bestStreak} detail="tracks" color="#16d9d2" /><StatTile label="Current streak" value={dash.stats.currentStreak} detail="tracks" color="#ff3b9d" /><StatTile label="Hottest track" value={dash.stats.hottestTrack} color="#ff793f" /></section></div><div className="mt-10 grid gap-6 lg:grid-cols-[1fr_.8fr]"><section className="ink-border bg-card p-6 md:p-8"><p className="zine-label">Achievements / earned & pending</p><h2 className="display mt-2 text-4xl">Proof of listening.</h2><div className="mt-7 space-y-4">{dash.achievements?.map((achievement, i) => <div key={achievement.id} data-testid={`achievement-${achievement.id}`}><div className="flex items-start gap-3"><div className={`mt-1 grid h-8 w-8 shrink-0 place-items-center border-2 border-foreground ${achievement.unlocked ? 'bg-primary' : 'bg-muted'}`}><Trophy size={15} /></div><div className="min-w-0 flex-1"><div className="flex justify-between gap-3"><strong>{achievement.name}</strong><span className="zine-label">{achievement.progress}/{achievement.target}</span></div><p className="mt-1 text-xs text-muted-foreground">{achievement.description}</p><div className="mt-2 h-2 border border-foreground bg-muted"><div className="h-full" style={{ width: `${Math.min(100, achievement.progress / achievement.target * 100)}%`, background: colors[i % colors.length] }} /></div></div></div></div>)}</div></section><section className="ink-border bg-[#c7ff23] p-6 md:p-8"><p className="zine-label">Recent activity / archive</p><h2 className="display mt-2 text-4xl">You were here.</h2><div className="mt-5 divide-y-2 divide-foreground">{activity?.slice(0, 6).map(item => <div className="py-4" key={item.id}><div className="flex items-center justify-between gap-3"><span className="text-sm font-bold">{item.title}</span><span className="zine-label">{new Date(item.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span></div><p className="mt-1 text-xs">{item.detail}</p></div>) || <p className="py-5 text-sm">Your listening history will print here.</p>}</div></section></div></PageFrame>;
}

function Router() {
  return <ErrorBoundary resetKey={window.location.pathname}><Switch><Route path="/" component={Overview} /><Route path="/discover" component={Discover} /><Route path="/game" component={Game} /><Route path="/leaderboard" component={Leaderboard} /><Route path="/library" component={Library} /><Route path="/profile" component={Profile} /><Route component={NotFound} /></Switch></ErrorBoundary>;
}

function App() {
  return <QueryClientProvider client={queryClient}><TooltipProvider><Shell><Router /></Shell><Toaster /></TooltipProvider></QueryClientProvider>;
}

export default App;