import re
import unicodedata

_STRIP_PARENS = re.compile(r"[\(\[][^\)\]]*[\)\]]")
_FEAT = re.compile(r"\b(feat|ft|featuring)\.?\b.*$")
_VERSION_SUFFIX = re.compile(r"\s-\s.*$")


def fold(value: str) -> str:
    """Lowercase, drop accents and punctuation: 'Tiësto' -> 'tiesto'."""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower().replace("&", " and ")).strip()


def slugify(value: str) -> str:
    return fold(value).replace(" ", "-")


def title_key(title: str) -> str:
    """Comparable form of a track title: ignores '(feat. X)', '- Remastered 2011' and punctuation."""
    t = _STRIP_PARENS.sub(" ", title)
    t = _VERSION_SUFFIX.sub("", t)
    t = _FEAT.sub("", fold(t))
    return fold(t)
