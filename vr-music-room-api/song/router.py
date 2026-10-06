from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User
from auth.jwt import get_current_user
from song.spotify_client import get_audio_features, get_track_info
from song.mood_mapper import map_mood
from song.lyrics_client import get_synced_lyrics
from song.lastfm_client import get_track_tags
from song.ai_analyzer import analyze_song_with_ai
from assets.matcher import match_assets

router = APIRouter(prefix="/song", tags=["Song Analysis"])

@router.get("/analyze/{track_id}")
def analyze_track(
    track_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The main brain — analyzes a track and returns mood, colors, lyrics, and matched assets."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.spotify_token:
        raise HTTPException(status_code=400, detail="Spotify not connected")

    token = user.spotify_token

    # 1. Get track info (name, artist, genres)
    track_info = get_track_info(track_id, token)
    if not track_info:
        raise HTTPException(status_code=404, detail="Track not found on Spotify")

    # 2. Get audio features (may be None if Spotify restricts access)
    features = get_audio_features(track_id, token)

    # 3. Get Last.fm tags
    lastfm_tags = get_track_tags(track_info["name"], track_info["artist"])

    # 4. Get synced lyrics
    duration_s = track_info["duration_ms"] // 1000
    lyrics = get_synced_lyrics(track_info["name"], track_info["artist"], duration_s)

    # 5. AI analysis of title + lyrics for better mood/color accuracy
    ai_analysis = analyze_song_with_ai(
        title=track_info["name"],
        artist=track_info["artist"],
        genres=track_info["genres"],
        lastfm_tags=lastfm_tags,
        lyrics_sample=lyrics.get("lines", []),
    )

    # 6. Map to mood — blends all sources, AI gets priority on colors
    mood = map_mood(features, track_info["genres"], lastfm_tags, ai_analysis)

    # 7. Find matching pre-made assets
    skyboxes = match_assets(mood["tags"], "skybox", db)
    textures = match_assets(mood["tags"], "texture", db)

    return {
        "track_id": track_id,
        "track_info": track_info,
        "analysis": features or {"note": "Audio features unavailable"},
        "lastfm_tags": lastfm_tags,
        "mood": mood,
        "lyrics": lyrics,
        "assets": {
            "skyboxes": skyboxes[:3],
            "textures": textures[:5],
            "needs_generation": len(skyboxes) == 0,
        },
    }