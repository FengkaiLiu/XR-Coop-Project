import os
import requests
from dotenv import load_dotenv

load_dotenv()

LASTFM_API = "http://ws.audioscrobbler.com/2.0/"
API_KEY = os.getenv("LASTFM_API_KEY")

def get_track_tags(track_name: str, artist_name: str) -> list:
    """Get community tags for a specific track."""
    resp = requests.get(LASTFM_API, params={
        "method": "track.getTopTags",
        "track": track_name,
        "artist": artist_name.split(",")[0].strip(),
        "api_key": API_KEY,
        "format": "json",
    })

    tags = _extract_tags(resp)
    if tags:
        return tags

    # Fallback: get artist-level tags if track tags are empty
    return get_artist_tags(artist_name)

def get_artist_tags(artist_name: str) -> list:
    """Get community tags for an artist."""
    resp = requests.get(LASTFM_API, params={
        "method": "artist.getTopTags",
        "artist": artist_name.split(",")[0].strip(),
        "api_key": API_KEY,
        "format": "json",
    })

    return _extract_tags(resp)

def _extract_tags(resp) -> list:
    """Extract tag names from Last.fm response."""
    if resp.status_code != 200:
        return []

    data = resp.json()

    # Track tags come under "toptags", artist tags under "toptags" too
    toptags = data.get("toptags", {})
    tag_list = toptags.get("tag", [])

    if not tag_list:
        return []

    # Return tags sorted by count (most popular first), lowercase
    tags = []
    for t in tag_list:
        name = t.get("name", "").lower().strip()
        count = int(t.get("count", 0))
        if name and count > 0:
            tags.append(name)

    return tags[:15]  # Top 15 tags