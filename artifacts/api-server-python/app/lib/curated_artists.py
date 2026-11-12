"""Artists the Spotify sync imports. Spotify's API (dev mode) returns no genres, so genres live here.

Names must match Spotify's artist names (the importer requires an exact, normalised match).
The first genre is the primary one and is used as the genre of each of the artist's tracks.
"""

CURATED_ARTISTS = [
    # House
    ("Fred again..", ["House", "Garage"]),
    ("Four Tet", ["House", "Ambient"]),
    ("Bicep", ["House", "Trance"]),
    ("salute", ["House", "Future Bass"]),
    ("Disclosure", ["House", "Garage"]),
    ("Daft Punk", ["House"]),
    ("FISHER", ["House"]),
    ("Duke Dumont", ["House"]),
    # Techno
    ("Charlotte de Witte", ["Techno", "Trance"]),
    ("Amelie Lens", ["Techno"]),
    ("Nina Kraviz", ["Techno"]),
    ("Adam Beyer", ["Techno"]),
    ("Richie Hawtin", ["Techno"]),
    ("Jeff Mills", ["Techno"]),
    ("Carl Cox", ["Techno", "House"]),
    ("Boris Brejcha", ["Techno"]),
    # Trance
    ("Armin van Buuren", ["Trance"]),
    ("Above & Beyond", ["Trance"]),
    ("Paul van Dyk", ["Trance"]),
    ("Ferry Corsten", ["Trance"]),
    ("Gareth Emery", ["Trance"]),
    ("Paul Oakenfold", ["Trance"]),
    ("ATB", ["Trance"]),
    ("Tiësto", ["Trance", "House"]),
    # Drum & Bass
    ("Pendulum", ["Drum & Bass"]),
    ("Chase & Status", ["Drum & Bass"]),
    ("Netsky", ["Drum & Bass"]),
    ("Sub Focus", ["Drum & Bass"]),
    ("Andy C", ["Drum & Bass"]),
    ("Noisia", ["Drum & Bass"]),
    ("Camo & Krooked", ["Drum & Bass"]),
    ("Wilkinson", ["Drum & Bass"]),
    # Dubstep
    ("Skrillex", ["Dubstep"]),
    ("Burial", ["Dubstep", "Garage"]),
    ("Excision", ["Dubstep"]),
    ("Flux Pavilion", ["Dubstep"]),
    ("Zomboy", ["Dubstep"]),
    ("Bassnectar", ["Dubstep"]),
    ("Skream", ["Dubstep"]),
    ("Rusko", ["Dubstep"]),
    # Future Bass
    ("Flume", ["Future Bass"]),
    ("Illenium", ["Future Bass"]),
    ("San Holo", ["Future Bass"]),
    ("Porter Robinson", ["Future Bass"]),
    ("Madeon", ["Future Bass", "House"]),
    ("Seven Lions", ["Future Bass"]),
    ("ODESZA", ["Future Bass"]),
    ("Louis The Child", ["Future Bass"]),
    # Garage
    ("Overmono", ["Garage", "Drum & Bass"]),
    ("Sammy Virji", ["Garage"]),
    ("Jamie xx", ["Garage", "House"]),
    ("Mura Masa", ["Garage"]),
    ("Interplanetary Criminal", ["Garage"]),
    ("Conducta", ["Garage"]),
    ("MJ Cole", ["Garage"]),
    ("Artful Dodger", ["Garage"]),
    # Ambient
    ("Aphex Twin", ["Ambient", "Techno"]),
    ("Brian Eno", ["Ambient"]),
    ("Boards of Canada", ["Ambient"]),
    ("Tycho", ["Ambient"]),
    ("Jon Hopkins", ["Ambient"]),
    ("Stars Of The Lid", ["Ambient"]),
    ("Biosphere", ["Ambient"]),
    ("Nils Frahm", ["Ambient"]),
]
