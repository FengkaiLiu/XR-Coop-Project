import re
import requests

LRCLIB_API = "https://lrclib.net/api"

def get_synced_lyrics(track_name: str, artist_name: str, duration_s: int) -> dict:
    """Fetch synced (timed) lyrics from lrclib."""
    resp = requests.get(
        f"{LRCLIB_API}/get",
        params={
            "track_name": track_name,
            "artist_name": artist_name.split(",")[0].strip(),  # Use first artist
            "duration": duration_s,
        },
    )

    if resp.status_code != 200:
        return {"synced": False, "lines": []}

    data = resp.json()
    synced_lyrics = data.get("syncedLyrics")
    plain_lyrics = data.get("plainLyrics")

    # Parse synced lyrics (LRC format: [mm:ss.xx] text)
    if synced_lyrics:
        lines = parse_lrc(synced_lyrics)
        return {"synced": True, "lines": lines}

    # Fallback: plain lyrics without timing
    if plain_lyrics:
        lines = [{"time_ms": 0, "text": line} for line in plain_lyrics.split("\n") if line.strip()]
        return {"synced": False, "lines": lines}

    return {"synced": False, "lines": []}

def parse_lrc(lrc_text: str) -> list:
    """Parse LRC format into [{time_ms, text}, ...]"""
    lines = []
    pattern = re.compile(r"\[(\d+):(\d+\.\d+)\](.*)")

    for line in lrc_text.split("\n"):
        match = pattern.match(line.strip())
        if match:
            minutes = int(match.group(1))
            seconds = float(match.group(2))
            text = match.group(3).strip()
            if text:  # Skip empty lines
                time_ms = int((minutes * 60 + seconds) * 1000)
                lines.append({"time_ms": time_ms, "text": text})

    return lines