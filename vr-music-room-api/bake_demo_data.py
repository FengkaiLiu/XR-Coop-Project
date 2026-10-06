"""
Pre-bake demo song data for offline VR playback.

Scans Assets/Audio/*.mp3, parses "Artist - Title.mp3" filenames, then for each:
  - reads duration via mutagen
  - fetches synced lyrics from lrclib
  - fetches tags from Last.fm
  - runs Gemini mood analysis
  - blends through mood_mapper

Writes per-track JSON + a library manifest into Assets/Resources/MoodData/,
matching the shape Unity's ApiClient already consumes (AnalyzeData / TrackListData).
"""
import json
import re
import sys
from pathlib import Path

from mutagen.mp3 import MP3

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from song.lyrics_client import get_synced_lyrics
from song.lastfm_client import get_track_tags
from song.ai_analyzer import analyze_song_with_ai
from song.mood_mapper import map_mood

UNITY_ROOT = HERE.parent
AUDIO_DIR = UNITY_ROOT / "Assets" / "Audio"
OUT_DIR = UNITY_ROOT / "Assets" / "Resources" / "MoodData"
TRACKS_DIR = OUT_DIR / "tracks"


def make_slug(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s


def parse_filename(path: Path):
    stem = path.stem
    if " - " in stem:
        artist, title = stem.split(" - ", 1)
    else:
        artist, title = "Unknown", stem
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
    return artist.strip(), title.strip()


def bake_one(mp3_path: Path) -> dict:
    artist, title = parse_filename(mp3_path)
    duration_s = int(MP3(str(mp3_path)).info.length)
    duration_ms = duration_s * 1000
    track_id = make_slug(f"{artist}-{title}")
    audio_file = mp3_path.name

    print(f"\n[{track_id}]")
    print(f"  {artist} - {title}  ({duration_s}s)")

    print("  lrclib   ...", end=" ", flush=True)
    try:
        lyrics = get_synced_lyrics(title, artist, duration_s)
        if lyrics["synced"]:
            print(f"SYNCED ({len(lyrics['lines'])} lines)")
        elif lyrics["lines"]:
            print(f"PLAIN  ({len(lyrics['lines'])} lines, unsynced)")
        else:
            print("NONE")
    except Exception as e:
        lyrics = {"synced": False, "lines": []}
        print(f"failed ({e})")

    print("  last.fm  ...", end=" ", flush=True)
    try:
        tags = get_track_tags(title, artist)
        print(f"{len(tags)} tags  {tags[:5]}")
    except Exception as e:
        tags = []
        print(f"failed ({e})")

    print("  gemini   ...", end=" ", flush=True)
    try:
        ai = analyze_song_with_ai(title, artist, [], tags, lyrics["lines"])
        if ai:
            print(f"{ai.get('primary_mood')} / {ai.get('atmosphere')}  {ai.get('color_palette')}")
        else:
            print("none (will fall back to genre/tag mapping)")
    except Exception as e:
        ai = None
        print(f"failed ({e})")

    mood = map_mood(None, [], tags, ai)

    return {
        "track_id": track_id,
        "audio_file": audio_file,
        "track_info": {
            "name": title,
            "artist": artist,
            "album_art": "",
            "duration_ms": duration_ms,
        },
        "mood": mood,
        "lyrics": lyrics,
    }


def main():
    if not AUDIO_DIR.exists():
        print(f"ERROR: audio dir not found: {AUDIO_DIR}")
        sys.exit(1)

    TRACKS_DIR.mkdir(parents=True, exist_ok=True)

    mp3s = sorted(AUDIO_DIR.glob("*.mp3"))
    print(f"Found {len(mp3s)} MP3s in {AUDIO_DIR}")

    library = []
    for mp3 in mp3s:
        try:
            data = bake_one(mp3)
        except Exception as e:
            print(f"  ! FAILED {mp3.name}: {e}")
            continue

        track_path = TRACKS_DIR / f"{data['track_id']}.json"
        track_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        library.append({
            "id": data["track_id"],
            "audio_file": data["audio_file"],
            "name": data["track_info"]["name"],
            "artist": data["track_info"]["artist"],
            "album_art": "",
            "duration_ms": data["track_info"]["duration_ms"],
        })

    (OUT_DIR / "library.json").write_text(
        json.dumps({"tracks": library}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n--- DONE ---")
    print(f"  {len(library)} tracks baked")
    print(f"  library:  {OUT_DIR / 'library.json'}")
    print(f"  per-track: {TRACKS_DIR}")


if __name__ == "__main__":
    main()
