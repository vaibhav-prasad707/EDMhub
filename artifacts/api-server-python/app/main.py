import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, SQLModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import edm, health
from app.db.models import Artist, Track
from app.db.session import engine
from app.lib.edm_data import get_artist_seed_rows, get_track_seed_rows


@asynccontextmanager
async def lifespan(_: FastAPI):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for row in get_artist_seed_rows():
            if not session.get(Artist, row["id"]):
                session.add(Artist(**row))
        session.commit()  # artists first: tracks reference them
        for row in get_track_seed_rows():
            if not session.get(Track, row["id"]):
                session.add(Track(**row))
        session.commit()
    yield


app = FastAPI(title="EDM Hub API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# Error bodies are {"error": "..."} with 400 for validation failures.
@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


app.include_router(health.router, prefix="/api")
app.include_router(edm.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
