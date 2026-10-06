import os
import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db.database import get_db
from db.models import User
from auth.jwt import get_current_user
from jose import jwt as jose_jwt

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
JWT_SECRET = os.getenv("JWT_SECRET", "fallback-secret")

SCOPES = "user-library-read user-read-playback-state user-read-currently-playing user-modify-playback-state"

router = APIRouter(prefix="/spotify", tags=["Spotify"])

@router.get("/connect")
def connect(token: str = ""):
    """Redirects to Spotify login. Pass ?token=your_jwt to link the right user."""
    url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&state={token}"
        f"&show_dialog=true"
    )
    return RedirectResponse(url)

@router.get("/callback")
def callback(code: str, state: str = "", db: Session = Depends(get_db)):
    """Spotify redirects here. Exchanges code for tokens and saves to user."""
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get Spotify tokens")

    tokens = resp.json()
    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token")

    # Find user from JWT in state param
    user = None
    if state:
        try:
            payload = jose_jwt.decode(state, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
            user = db.query(User).filter(User.id == user_id).first()
        except Exception:
            pass

    # Fallback: first user
    if not user:
        user = db.query(User).first()

    if user:
        user.spotify_token = access_token
        user.spotify_refresh = refresh_token
        db.commit()

    # Redirect back to demo page
    return RedirectResponse("/demo?spotify=connected")

@router.get("/library")
def get_library(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch user's saved/liked tracks from Spotify."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.spotify_token:
        raise HTTPException(status_code=400, detail="Spotify not connected")

    resp = requests.get(
        "https://api.spotify.com/v1/me/tracks?limit=50",
        headers={"Authorization": f"Bearer {user.spotify_token}"},
    )

    if resp.status_code == 401:
        new_token = refresh_spotify_token(user, db)
        resp = requests.get(
            "https://api.spotify.com/v1/me/tracks?limit=50",
            headers={"Authorization": f"Bearer {new_token}"},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch Spotify library")

    data = resp.json()
    tracks = []
    for item in data.get("items", []):
        t = item["track"]
        tracks.append({
            "spotify_id": t["id"],
            "name": t["name"],
            "artist": ", ".join(a["name"] for a in t["artists"]),
            "album_art": t["album"]["images"][0]["url"] if t["album"]["images"] else None,
            "duration_ms": t["duration_ms"],
        })

    return {"tracks": tracks}

def refresh_spotify_token(user: User, db: Session) -> str:
    """Use refresh token to get a new access token."""
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": user.spotify_refresh,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to refresh Spotify token")

    tokens = resp.json()
    user.spotify_token = tokens["access_token"]
    if "refresh_token" in tokens:
        user.spotify_refresh = tokens["refresh_token"]
    db.commit()
    return tokens["access_token"]