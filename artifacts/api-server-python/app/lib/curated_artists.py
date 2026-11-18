"""Artists the Spotify sync imports. Spotify's API (dev mode) returns no genres, so genres live here.

Each section's name is the primary genre of its artists; "(+ a, b)" adds secondary genres.
An artist listed in several sections is imported once: their genres are merged, and the section
they appear in first (sections run in the order below) gives their primary genre.
Names must match Spotify's artist names (the importer requires an exact, normalised match).

`CURATED_ARTISTS` is the result, as [(name, [genres])], interleaved across sections so the first
artists shown in the app span every genre instead of one genre at a time.
"""
from typing import Dict, List, Tuple

# Secondary tags that are spelled differently from the app's main genre names.
GENRE_ALIASES = {"uk garage": "Garage", "garage": "Garage"}

SECTIONS: List[Tuple[str, str]] = [
    ("House", """
Fred again.. (+ UK Garage)
Four Tet (+ Ambient, UK Garage)
Bicep (+ Trance, Breakbeat)
salute (+ UK Garage, Future Bass)
Disclosure (+ UK Garage)
Daft Punk (+ French House)
FISHER
Duke Dumont
Calvin Harris (+ EDM)
Swedish House Mafia (+ Progressive House)
David Guetta (+ EDM)
Eric Prydz (+ Progressive House, Techno)
deadmau5 (+ Progressive House)
Carl Cox (+ Techno)
Jamie xx (+ UK Garage)
MK
Gorgon City (+ UK Garage)
Chris Lake
John Summit
Dom Dolla
Mau P
CamelPhat
MEDUZA
Vintage Culture
Purple Disco Machine (+ Nu-Disco)
Peggy Gou (+ Techno)
Honey Dijon
Green Velvet
Dennis Ferrer
Kerri Chandler
Louie Vega
Masters At Work
Frankie Knuckles
Larry Heard
Todd Terry
Roger Sanchez
Armand Van Helden
Bob Sinclar
Claptone
Solomun (+ Melodic Techno)
Dixon (+ Melodic House)
Âme (+ Melodic House)
Black Coffee (+ Afro House)
Keinemusik
&ME
Rampa
Adam Port
ANOTR
Josh Baker
Dennis Cruz
"""),
    ("Techno", """
Charlotte de Witte (+ Trance)
Amelie Lens
Nina Kraviz
Adam Beyer
Richie Hawtin
Jeff Mills
Carl Cox (+ House)
Boris Brejcha
Adam Port (+ Melodic House)
Sven Väth
Solomun (+ House)
Maceo Plex
Tale Of Us (+ Melodic Techno)
Anyma (+ Melodic Techno)
ARTBAT (+ Melodic Techno)
Adriatique (+ Melodic Techno)
Stephan Bodzin
Ben Klock
Marcel Dettmann
Dax J
Paula Temple
Rebekah
SPFDJ
I Hate Models
Klangkuenstler
999999999
SNTS
DVS1
Oscar Mulero
Surgeon
Luke Slater
Regis
Chris Liebing
Joseph Capriati
Enrico Sangiuliano
Marco Carola
Joseph Ray
ANNA
Reinier Zonneveld
UMEK
Deborah De Luca
Indira Paganotto (+ Psytrance)
Alignment
Kobosil
FJAAK
Pan-Pot
Township Rebellion
Joris Voorn
ART DEPARTMENT
Laurent Garnier
"""),
    ("Trance", """
Armin van Buuren
Above & Beyond
Paul van Dyk
Ferry Corsten
Gareth Emery
Paul Oakenfold
ATB
Tiësto (+ House, Progressive Trance)
Aly & Fila
Giuseppe Ottaviani
Markus Schulz
Cosmic Gate
Dash Berlin
Andrew Rayel
MaRLo
Craig Connelly
John O'Callaghan
Bryan Kearney
Factor B
Jorn van Deynhoven
Solarstone
Robert Nickson
Rank 1
Push
System F
Chicane
Lange
Signum
Johan Gielen
DJ Shah
Alex M.O.R.P.H.
Stoneface & Terminal
Sneijder
Sean Tyas
Simon Patterson
Will Atkinson
RAM
ReOrder
Ben Gold
Ruben de Ronde
ilan Bluestone
Jason Ross
Seven Lions (+ Future Bass)
Porter Robinson (+ Future Bass)
OceanLab
Orjan Nilsen
Ferry Tayle
Paul Denton
"""),
    ("Drum & Bass", """
Pendulum
Chase & Status
Netsky
Sub Focus
Andy C
Noisia
Camo & Krooked
Wilkinson
Dimension
Culture Shock
Metrik
Hybrid Minds
Kanine
A.M.C
Hedex
Bou
Mozey
Alcemist
Simula
S.P.Y
Calibre
Break
Lenzman
SpectraSoul
High Contrast
London Elektricity
Goldie
Roni Size
LTJ Bukem
Shy FX
DJ Hype
DJ Fresh
Friction
Drumsound & Bassline Smith
The Prototypes
Delta Heavy
Matrix & Futurebound
Fred V
Grafix
Maduk
Feint
Fox Stevenson (+ Dubstep, Bass House)
MUZZ
Black Sun Empire
Phace
Mefjus
State of Mind
Ed Rush & Optical
Dom & Roland
Spor
"""),
    ("Dubstep", """
Skrillex
Burial (+ UK Garage, Ambient)
Excision
Flux Pavilion
Zomboy
Bassnectar
Skream
Rusko
Virtual Riot
MUST DIE!
Wooli
Subtronics
Svdden Death
Marauda
Kai Wachi
Sullivan King
REZZ (+ Midtempo Bass)
ATLiens
Ganja White Night
Liquid Stranger
LSDREAM
GRiZ (+ Funk, Future Bass)
Zeds Dead
12th Planet
Doctor P
Cookie Monsta
FuntCase
Modestep
Barely Alive
Eptic
Habstrakt (+ Bass House)
Getter
Virtual Self (+ Future Bass)
Space Laces
Kill The Noise
NGHTMRE (+ Trap)
SLANDER (+ Future Bass)
Kompany
Calcium
YOOKiE
Hi I'm Ghost
HOL!
HOLLY
Trampa
TYNAN
Peekaboo
Of The Trees
Distinct Motive
Truth
"""),
    ("Future Bass", """
Flume
Illenium
San Holo
Porter Robinson
Madeon (+ House)
Seven Lions (+ Trance)
ODESZA
Louis The Child
The Chainsmokers (+ EDM, Progressive House)
Marshmello (+ Future House)
Gryffin (+ Progressive House)
Said The Sky
Dabin
Jai Wolf
Ekali
QUIX
Alison Wonderland (+ Trap)
What So Not
RL Grime (+ Trap)
Cashmere Cat
Mura Masa (+ UK Garage)
Petit Biscuit
Whethan
Juelz
DROELOE
Taska Black
Manila Killa
Wave Racer
MEMBA
Big Wild
Kasbo
Slow Magic
Robotaki
Throttle
NGHTMRE (+ Dubstep)
SLANDER (+ Dubstep)
ARMNHMR
Nurko
William Black
Trivecta
Jason Ross (+ Trance)
Blanke
Adventure Club
RÜFÜS DU SOL (+ Melodic House)
The Knocks (+ Disco House)
Krewella (+ EDM)
Cash Cash
DVBBS
Audien (+ Progressive House)
"""),
    ("Garage", """
Overmono (+ Drum & Bass)
Sammy Virji
Jamie xx (+ House)
Mura Masa
Interplanetary Criminal
Conducta
MJ Cole
Artful Dodger
DJ EZ
Todd Edwards
Burial (+ Dubstep, Ambient)
El-B
Zed Bias
Wookie
Horsepower Productions
The Streets
Craig David
T2
DJ Q
Preditah
Flava D
Champion
Pangaea
Pearson Sound
Joy Orbison
Ben UFO
Floating Points (+ Ambient, House)
Dusky (+ House)
Bklava
Notion
MPH
Silva Bumpa
Dr Dubplate
Main Phase
Bakey
Bushbaby
Oppidan
Prozak
Chris Lorenzo (+ Bass House)
AC Slater (+ Bass House)
Taiki Nulight
Holy Goof
Darkzy
Skepsis
DJ Zinc
DJ Seinfeld (+ Lo-Fi House)
Mall Grab (+ House)
Ross From Friends (+ Lo-Fi House)
Logic1000
salute (+ House)
"""),
    ("Ambient", """
Aphex Twin (+ Techno, IDM)
Brian Eno
Boards of Canada
Tycho
Jon Hopkins
Stars Of The Lid
Biosphere
Nils Frahm
Max Richter
Ólafur Arnalds
Hania Rani
Kiasmos (+ Melodic Techno)
Rival Consoles
Floating Points (+ House)
Four Tet (+ House)
Autechre
Squarepusher (+ IDM, Drum & Bass)
Amon Tobin
Oneohtrix Point Never
Tim Hecker
Fennesz
William Basinski
Loscil
Gas
The Orb
The Future Sound of London
Global Communication
Tangerine Dream
Klaus Schulze
Vangelis
Jean-Michel Jarre
Suzanne Ciani
Hiroshi Yoshimura
Ryuichi Sakamoto
Kitaro
Laraaji
Harold Budd
Jóhann Jóhannsson
Alessandro Cortini
Daniel Avery (+ Techno)
Kelly Lee Owens (+ Techno)
Actress
Laurel Halo
Caterina Barbieri
Kaitlyn Aurelia Smith
Julianna Barwick
Grouper
The Album Leaf
Hammock
Marconi Union
"""),
]


def _norm_genre(tag: str) -> str:
    tag = tag.strip()
    return GENRE_ALIASES.get(tag.lower(), tag)


def _parse_line(line: str, section_genre: str) -> Tuple[str, List[str]]:
    name, _, rest = line.partition(" (+ ")
    tags = [t for t in rest.rstrip(")").split(",")] if rest else []
    genres: List[str] = []
    for g in [section_genre, *tags]:
        g = _norm_genre(g)
        if g and g not in genres:
            genres.append(g)
    return name.strip(), genres


def build_curated(sections: List[Tuple[str, str]]) -> List[Tuple[str, List[str]]]:
    from app.lib.text import fold

    merged: Dict[str, Tuple[str, List[str]]] = {}
    queues: List[List[str]] = []
    for section_genre, block in sections:
        queue: List[str] = []
        for raw in block.strip().splitlines():
            if not raw.strip():
                continue
            name, genres = _parse_line(raw.strip(), section_genre)
            key = fold(name)
            if key in merged:  # already listed: merge genres, keep the original primary genre
                known = merged[key][1]
                known.extend(g for g in genres if g not in known)
            else:
                merged[key] = (name, genres)
                queue.append(key)
        queues.append(queue)

    ordered: List[Tuple[str, List[str]]] = []
    for rank in range(max(len(q) for q in queues)):
        for queue in queues:
            if rank < len(queue):
                ordered.append(merged[queue[rank]])
    return ordered


CURATED_ARTISTS: List[Tuple[str, List[str]]] = build_curated(SECTIONS)
