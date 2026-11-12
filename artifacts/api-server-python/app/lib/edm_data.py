from typing import List, Dict, Any, Optional

IMAGE_URLS = [
    "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1571266028243-d220c2a0f6d5?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1524368535928-5b5e00ddc76b?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1531058020387-3be344556be6?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?auto=format&fit=crop&w=900&q=85",
    "https://images.unsplash.com/photo-1521337581100-8ca9a73a5f79?auto=format&fit=crop&w=900&q=85",
]

GENRES = [
    {"id": "house", "name": "House", "count": 148},
    {"id": "techno", "name": "Techno", "count": 112},
    {"id": "trance", "name": "Trance", "count": 94},
    {"id": "dnb", "name": "Drum & Bass", "count": 87},
    {"id": "dubstep", "name": "Dubstep", "count": 76},
    {"id": "future-bass", "name": "Future Bass", "count": 62},
    {"id": "garage", "name": "Garage", "count": 44},
    {"id": "ambient", "name": "Ambient", "count": 31},
]

# Royalty-free placeholder audio (SoundHelix demo songs, https://www.soundhelix.com).
# These are NOT the actual tracks; they stand in until real previews are imported.
PREVIEW_URLS = [
    f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{n}.mp3" for n in range(1, 17)
]

ARTIST_SEEDS = [
    {
        "id": "fred-again",
        "name": "Fred again..",
        "bio": "Emotional club music built from voice notes, found sounds, and the beautiful mess of real life.",
        "genres": ["House", "Garage"],
        "followers": "4.2M",
        "accent": "#D6FF00",
        "track": ["places to be", "House", 2024, "03:46", "#20D6C7"],
    },
    {
        "id": "charlotte-de-witte",
        "name": "Charlotte de Witte",
        "bio": "A relentlessly driving techno force with an instinct for the moments that turn a room inside out.",
        "genres": ["Techno", "Trance"],
        "followers": "2.1M",
        "accent": "#FF3C8B",
        "track": ["The Age Of Love", "Techno", 2022, "06:14", "#FF3C8B"],
    },
    {
        "id": "four-tet",
        "name": "Four Tet",
        "bio": "Warm, strange, endlessly curious dance music that folds folk, jazz, garage, and ambient into one orbit.",
        "genres": ["House", "Ambient"],
        "followers": "1.8M",
        "accent": "#19D3D1",
        "track": ["Baby", "House", 2024, "04:32", "#19D3D1"],
    },
    {
        "id": "overmono",
        "name": "Overmono",
        "bio": "UK club music with a pulse: euphoric breaks, distorted memories, and bass built for the late train home.",
        "genres": ["Garage", "Drum & Bass"],
        "followers": "682K",
        "accent": "#FF8A1F",
        "track": ["Good Lies", "Garage", 2023, "04:09", "#FF8A1F"],
    },
    {
        "id": "salute",
        "name": "salute",
        "bio": "Joyful, high-definition dance music for the people who never stopped believing in a big chorus.",
        "genres": ["House", "Future Bass"],
        "followers": "421K",
        "accent": "#9B8CFF",
        "track": ["saving flowers", "House", 2024, "03:28", "#9B8CFF"],
    },
    {
        "id": "burial",
        "name": "Burial",
        "bio": "Rain-soaked dubstep and ghosted-out garage from the edges of the city after midnight.",
        "genres": ["Dubstep", "Garage"],
        "followers": "1.1M",
        "accent": "#D6FF00",
        "track": ["Archangel", "Dubstep", 2007, "03:59", "#D6FF00"],
    },
    {
        "id": "bicep",
        "name": "Bicep",
        "bio": "A widescreen rush of breakbeat, synths, and hands-in-the-air release, built for the biggest rooms.",
        "genres": ["House", "Trance"],
        "followers": "1.3M",
        "accent": "#FF3C8B",
        "track": ["Glue", "House", 2017, "04:36", "#FF3C8B"],
    },
    {
        "id": "aphex-twin",
        "name": "Aphex Twin",
        "bio": "The unpredictable electronic polymath whose strange machines still make the future sound immediate.",
        "genres": ["Ambient", "Techno"],
        "followers": "1.5M",
        "accent": "#19D3D1",
        "track": ["Xtal", "Ambient", 1992, "04:54", "#19D3D1"],
    },
]

EXTRA_TRACK_NAMES = [
    ["Delilah (pull me out of this)", "House", 2022, "04:10", "#D6FF00"],
    ["The Walls", "Garage", 2024, "03:52", "#20D6C7"],
    ["Dopamine", "Techno", 2023, "05:28", "#FF3C8B"],
    ["Love Hz", "Trance", 2021, "06:04", "#9B8CFF"],
    ["Two Thousand and Seventeen", "Ambient", 2017, "04:21", "#19D3D1"],
    ["So U Kno", "Garage", 2020, "04:45", "#FF8A1F"],
    ["Apricots", "House", 2021, "04:13", "#FF8A1F"],
    ["Heliosphan", "Ambient", 1994, "04:46", "#D6FF00"],
]

def get_artist_seed_rows() -> List[Dict[str, Any]]:
    return [
        {
            "id": artist["id"],
            "name": artist["name"],
            "image_url": IMAGE_URLS[i],
            "bio": artist["bio"],
            "genres": list(artist["genres"]),
            "followers": artist["followers"],
            "accent": artist["accent"],
        }
        for i, artist in enumerate(ARTIST_SEEDS)
    ]


def get_track_seed_rows() -> List[Dict[str, Any]]:
    rows = []
    for i, artist in enumerate(ARTIST_SEEDS):
        title, genre, year, duration, color = artist["track"]
        rows.append({
            "id": f"{artist['id']}-top",
            "title": title,
            "artist_id": artist["id"],
            "genre": genre,
            "release_year": year,
            "duration": duration,
            "color": color,
            "preview_url": PREVIEW_URLS[i * 2],
        })
        title, genre, year, duration, color = EXTRA_TRACK_NAMES[i]
        rows.append({
            "id": f"{artist['id']}-alt",
            "title": title,
            "artist_id": artist["id"],
            "genre": genre,
            "release_year": year,
            "duration": duration,
            "color": color,
            "preview_url": PREVIEW_URLS[i * 2 + 1],
        })
    return rows


# --- In-memory catalog served by the API (camelCase, matches the OpenAPI contract) ---

_ARTIST_NAMES = {a["id"]: a["name"] for a in ARTIST_SEEDS}

API_TRACKS: List[Dict[str, Any]] = [
    {
        "id": t["id"],
        "title": t["title"],
        "artistName": _ARTIST_NAMES.get(t["artist_id"], ""),
        "genre": t["genre"],
        "releaseYear": t["release_year"],
        "duration": t["duration"],
        "color": t["color"],
        "previewUrl": t["preview_url"],
    }
    for t in get_track_seed_rows()
]

_TRACKS_BY_ID = {t["id"]: t for t in API_TRACKS}

API_ARTISTS: List[Dict[str, Any]] = [
    {
        "id": a["id"],
        "name": a["name"],
        "imageUrl": a["image_url"],
        "bio": a["bio"],
        "genres": a["genres"],
        "followers": a["followers"],
        "accent": a["accent"],
        "topTrack": _TRACKS_BY_ID[f"{a['id']}-top"],
    }
    for a in get_artist_seed_rows()
]


def get_artist(artist_id: str) -> Optional[Dict[str, Any]]:
    return next((a for a in API_ARTISTS if a["id"] == artist_id), None)
