from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import edm, health
from app.db.session import engine
from app.db.models import SQLModel
from app.lib.edm_data import get_artist_seed_rows, get_track_seed_rows
from sqlmodel import Session

app = FastAPI(title="EDM Hub API")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(edm.router, prefix="/api")
app.include_router(health.router)

@app.on_event("startup")
def on_startup():
    # Create tables
    SQLModel.metadata.create_all(engine)

    # Seed data
    with Session(engine) as session:
        # Seed Artists
        artists = get_artist_seed_rows()
        for artist_data in artists:
            # Using simple existence check to avoid duplicates
            from app.db.models import Artist
            existing = session.get(Artist, artist_data["id"])
            if not existing:
                session.add(Artist(**artist_data))

        # Seed Tracks
        tracks = get_track_seed_rows()
        for track_data in tracks:
            from app.db.models import Track
            existing = session.get(Track, track_data["id"])
            if not existing:
                session.add(Track(**track_data))

        session.commit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
