from sqlmodel import Session, create_engine

from app.core.config import settings


def _normalize_url(url: str) -> str:
    # Accept the standard postgresql:// / postgres:// forms and pin the psycopg2 driver.
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


engine = create_engine(_normalize_url(settings.DATABASE_URL), echo=False)


def get_session():
    with Session(engine) as session:
        yield session
