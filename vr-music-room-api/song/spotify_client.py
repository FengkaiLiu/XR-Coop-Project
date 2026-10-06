import requests

SPOTIFY_API = "https://api.spotify.com/v1"

def get_audio_features(track_id: str, token: str) -> dict:
    """Get tempo, energy, valence, danceability, etc. for a track."""
    resp = requests.get(
        f"{SPOTIFY_API}/audio-features/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        print(f"[Audio Features] Not available (status {resp.status_code}) — will use genre fallback")
        return None

    data = resp.json()
    return {
        "tempo": data.get("tempo"),
        "energy": data.get("energy"),
        "valence": data.get("valence"),
        "danceability": data.get("danceability"),
        "acousticness": data.get("acousticness"),
        "instrumentalness": data.get("instrumentalness"),
        "key": data.get("key"),
        "mode": data.get("mode"),
    }

def get_track_info(track_id: str, token: str) -> dict:
    """Get track name, artist, genres (via artist), album art."""
    resp = requests.get(
        f"{SPOTIFY_API}/tracks/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        return None

    track = resp.json()
    artist_id = track["artists"][0]["id"]

    # Get artist to pull genres
    artist_resp = requests.get(
        f"{SPOTIFY_API}/artists/{artist_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    genres = artist_resp.json().get("genres", []) if artist_resp.status_code == 200 else []

    return {
        "name": track["name"],
        "artist": ", ".join(a["name"] for a in track["artists"]),
        "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
        "duration_ms": track["duration_ms"],
        "genres": genres,
    }

def play_track(track_id: str, token: str) -> bool:
    """Start playing a track, waking up the device if needed."""
    # First try normal play
    resp = requests.put(
        f"{SPOTIFY_API}/me/player/play",
        headers={"Authorization": f"Bearer {token}"},
        json={"uris": [f"spotify:track:{track_id}"]},
    )
    if resp.status_code == 204:
        return True

    # If no active device, find one and transfer playback
    if resp.status_code in (404, 403):
        devices = get_available_devices(token)
        if devices:
            device_id = devices[0]["id"]
            # Transfer playback to wake it up
            requests.put(
                f"{SPOTIFY_API}/me/player",
                headers={"Authorization": f"Bearer {token}"},
                json={"device_ids": [device_id], "play": False},
            )
            # Retry play
            resp = requests.put(
                f"{SPOTIFY_API}/me/player/play",
                headers={"Authorization": f"Bearer {token}"},
                json={"uris": [f"spotify:track:{track_id}"]},
            )
            if resp.status_code == 204:
                return True

    print(f"[Play] Failed (status {resp.status_code}): {resp.text}")
    return False


def get_available_devices(token: str) -> list:
    """Get list of available Spotify devices."""
    resp = requests.get(
        f"{SPOTIFY_API}/me/player/devices",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("devices", [])

def get_playback_state(token: str) -> dict:
    """Get current playback position and state."""
    resp = requests.get(
        f"{SPOTIFY_API}/me/player",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    return {
        "is_playing": data.get("is_playing", False),
        "progress_ms": data.get("progress_ms", 0),
        "track_id": data.get("item", {}).get("id", ""),
    }

def pause_playback(token: str) -> bool:
    resp = requests.put(
        f"{SPOTIFY_API}/me/player/pause",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 204:
        print(f"[Pause] Failed (status {resp.status_code}): {resp.text}")
    return resp.status_code == 204

def resume_playback(token: str) -> bool:
    resp = requests.put(
        f"{SPOTIFY_API}/me/player/play",
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.status_code == 204

def get_user_library(token: str, limit: int = 50) -> list:
    """Get user's saved tracks (Liked Songs)."""
    resp = requests.get(
        f"{SPOTIFY_API}/me/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": limit},
    )
    if resp.status_code != 200:
        print(f"[Library] Failed (status {resp.status_code})")
        return []

    items = resp.json().get("items", [])
    tracks = []
    for item in items:
        t = item["track"]
        tracks.append({
            "id": t["id"],
            "name": t["name"],
            "artist": ", ".join(a["name"] for a in t["artists"]),
            "album_art": t["album"]["images"][0]["url"] if t["album"]["images"] else None,
            "duration_ms": t["duration_ms"],
        })
    return tracks