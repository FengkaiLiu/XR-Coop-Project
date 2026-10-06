from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from db.database import engine, Base
from auth.router import router as auth_router
from auth.spotify_oauth import router as spotify_router
from song.router import router as song_router
from assets.router import router as assets_router
from db.database import get_db
from db.models import User
from song.spotify_client import get_user_library
from song.router import analyze_track
from song.spotify_client import get_user_library, play_track, get_playback_state, pause_playback, resume_playback

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VR Music Room API")

# Allow Quest to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(spotify_router)
app.include_router(song_router)
app.include_router(assets_router)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"status": "running", "message": "VR Music Room API is live"}

@app.get("/demo")
def demo():
    return FileResponse("static/demo.html")

@app.get("/test/mood")
async def test_mood():
    return {
        "song": "Test Song",
        "artist": "Test Artist",
        "primary_mood": "dreamy",
        "atmosphere": "dreamy",
        "emotional_tone": "peaceful",
        "energy_level": 0.4,
        "color_palette": ["#6A5ACD", "#4B3D8F", "#8B7EC8", "#2E1F5E"],
        "mood_tags": ["calm", "ethereal", "ambient"],
        "album_art_url": "",
        "lyrics": {
            "synced": True,
            "lines": [
                {"time_ms": 0, "text": "Welcome to the dream"},
                {"time_ms": 3000, "text": "Floating through the night"},
                {"time_ms": 6000, "text": "Colors in the sky"},
                {"time_ms": 9000, "text": "Everything feels right"},
                {"time_ms": 12000, "text": "Lost in the rhythm"},
                {"time_ms": 15000, "text": "Dancing with the stars"},
            ]
        }
    }

@app.get("/dev/library")
def dev_library():
    db = next(get_db())
    try:
        user = db.query(User).filter(User.spotify_token.isnot(None)).first()
        if not user:
            return {"error": "No user with Spotify connected. Log in via /demo first."}
        tracks = get_user_library(user.spotify_token)
        return {"tracks": tracks}
    finally:
        db.close()

@app.get("/dev/play/{track_id}")
def dev_play(track_id: str):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.spotify_token.isnot(None)).first()
        if not user:
            return {"error": "No user with Spotify connected."}
        success = play_track(track_id, user.spotify_token)
        return {"playing": success, "track_id": track_id}
    finally:
        db.close()

@app.get("/dev/playback")
def dev_playback():
    db = next(get_db())
    try:
        user = db.query(User).filter(User.spotify_token.isnot(None)).first()
        if not user:
            return {"error": "No user with Spotify connected."}
        state = get_playback_state(user.spotify_token)
        return state or {"is_playing": False, "progress_ms": 0}
    finally:
        db.close()

@app.get("/dev/pause")
def dev_pause():
    db = next(get_db())
    try:
        user = db.query(User).filter(User.spotify_token.isnot(None)).first()
        if not user:
            return {"error": "No user with Spotify connected."}
        return {"paused": pause_playback(user.spotify_token)}
    finally:
        db.close()

@app.get("/dev/resume")
def dev_resume():
    db = next(get_db())
    try:
        user = db.query(User).filter(User.spotify_token.isnot(None)).first()
        if not user:
            return {"error": "No user with Spotify connected."}
        return {"resumed": resume_playback(user.spotify_token)}
    finally:
        db.close()

@app.get("/dev/analyze/{track_id}")
def dev_analyze(track_id: str):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.spotify_token.isnot(None)).first()
        if not user:
            return {"error": "No user with Spotify connected. Log in via /demo first."}
        return analyze_track(track_id, user.id, db)
    finally:
        db.close()