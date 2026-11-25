import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, SQLModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, edm, health, library, spotify
from app.db.models import Artist, Track
from app.db.migrate import apply_migrations
from app.db.session import engine
from app.lib.edm_data import get_artist_seed_rows, get_track_seed_rows


def insert_if_missing(session: Session, model, row: dict) -> None:
    # Never overwrite: imported/edited catalog data must survive restarts.
    if session.get(model, row["id"]) is None:
        session.add(model(**row))


@asynccontextmanager
async def lifespan(_: FastAPI):
    SQLModel.metadata.create_all(engine)
    apply_migrations(engine)
    with Session(engine) as session:
        for row in get_artist_seed_rows():
            insert_if_missing(session, Artist, row)
        session.commit()  # artists first: tracks reference them
        for row in get_track_seed_rows():
            insert_if_missing(session, Track, row)
        session.commit()
    yield


app = FastAPI(title="EDM Hub API", lifespan=lifespan)

# The frontend reaches the API through a same-origin proxy, so CORS is only needed for
# explicitly listed origins (credentials are never allowed for "*").
_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware, allow_origins=_origins, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )


# Error bodies are {"error": "..."} with 400 for validation failures.
@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(edm.router, prefix="/api")
app.include_router(library.router, prefix="/api")
app.include_router(spotify.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
